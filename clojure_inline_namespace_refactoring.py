import sublime, sublime_plugin
import re

class ClojureInlineNamespaceRefactoringCommand(sublime_plugin.TextCommand):

	__ns_class = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END

	def run(self, edit):
		print("ClojureNsExtractor called")
		v = self.view

		# get namespace text
		inline_region = self.find_ns_modification(self.view.sel()[0].begin())
		print("[inline phrase = {0}]".format(v.substr(inline_region)))
		if inline_region.begin() == inline_region.end():
			sublime.error_message("No namespace phrase at current cursol position.")
			return

		if v.substr(inline_region.end()) == "/":
			self.extract_inline_ns_modification(edit, inline_region)
		else:
			self.extract_inline_pkg_modification(edit, inline_region)
		print("ClojureNsExtractor finished")

	def find_ns_modification(self, pos):
		v = self.view
		r = v.expand_by_class(pos, self.__class__.__ns_class, " /({[")
		return v.find(r"[-\w\d.]+[-\w\d]", r.begin())

	def current_file_namespace(self):
		f = self.view.file_name();
		f = re.sub(r"^.+\/src\/(.+)\.clj\w?$", r"\1", f)
		f = re.sub("_", "-", f)
		f = re.sub("/", ".", f)
		return f

	def extract_inline_pkg_modification(self, edit, inline_region):
		v = self.view

		fqcn = v.substr(inline_region)
		parts = fqcn.split(".")
		if len(parts) < 2:
			return
		pkgname = ".".join(parts[:-1])
		classname = parts[-1]
		print("[pkgname, classname = {0}, {1}]".format(pkgname, classname))

		# 2. insert "import" phrase in ns form
		ns_and_the_1st_arg_region = v.find(r"\(ns[,\s]+[^,\s]+", 0)
		import_region = v.find(r"\(ns[,\s](.|\n)+\(:import[\s,][^)]+?\)", 0)
		print("import code region: " + str(import_region))
		if ns_and_the_1st_arg_region.end() < 0:
			# 2-1. There id no ns form
			end_of_shebang_or_dependencies_regions = v.find_all(r"^(#!.+|'\{:dependencies(.|\n)+?\})")
			if len(end_of_shebang_or_dependencies_regions) > 0:
				# 2-1-1. There are shebang or dependencies
				import_code = "\n(import '({0} {1}))".format(pkgname, classname)
				import_code_insertion_pos = end_of_shebang_or_dependencies_regions[-1].end()
			else:
				# 2-1-2. There are not any shebang or dependencies or ns form.
				current_ns = self.current_file_namespace()
				import_code = "(ns {0}\n  (:import ({1} {2})))\n".format(current_ns, pkgname, classname)
				import_code_insertion_pos = 0
			v.insert(edit, import_code_insertion_pos, import_code)
			added_import_alias_end_pos = import_code_insertion_pos + len(import_code) - 3
		elif import_region.end() < 0:
			# 2-2. There is no ":import" in ns form
			import_code = "\n  (:import ({0} {1}))".format(pkgname, classname)
			import_code_insertion_pos = ns_and_the_1st_arg_region.end()
			v.insert(edit, import_code_insertion_pos, import_code)
			added_import_alias_end_pos = import_code_insertion_pos + len(import_code) - 2
		else:
			# 2-3. There is ":import" in ns form
			import_code = "\n           ({0} {1})".format(pkgname, classname)
			import_code_insertion_pos = import_region.end() - 1
			v.insert(edit, import_code_insertion_pos, import_code)
			added_import_alias_end_pos = import_code_insertion_pos + len(import_code) - 1

		# replace all of the inlines
		fqcn_regexp = fqcn.replace(".", "\.") # TODO: general and safe way to `string -> regexp` conversion
		for i in range(len(v.find_all(fqcn_regexp))):
			fqcn_region = v.find(fqcn_regexp, 0)
			v.replace(edit, fqcn_region, classname)

	def extract_inline_ns_modification(self, edit, inline_region):
		v = self.view

		replaced_regions = []
		ns = v.substr(inline_region)
		alias = ns.split(".")[-1]
		print("[ns, alias = {0}, {1}]".format(ns, alias))

		# 2. insert "require" phrase in ns form
		ns_and_the_1st_arg_region = v.find(r"\(ns[,\s]+[^,\s]+", 0)
		require_region = v.find(r"\(ns[,\s](.|\n)+\(:require[\s,][^)]+?\)", 0)
		print("require code region: " + str(require_region))
		if ns_and_the_1st_arg_region.end() < 0:
			# 2-1. There id no ns form
			end_of_shebang_or_dependencies_regions = v.find_all(r"^(#!.+|'\{:dependencies(.|\n)+?\})")
			if len(end_of_shebang_or_dependencies_regions) > 0:
				# 2-1-1. There are shebang or dependencies
				require_code = "\n(require '[{0} :as {1}])".format(ns, alias)
				require_code_insertion_pos = end_of_shebang_or_dependencies_regions[-1].end()
			else:
				# 2-1-2. There are not any shebang or dependencies or ns form.
				current_ns = self.current_file_namespace()
				require_code = "(ns {0}\n  (:require [{1} :as {2}]))\n".format(current_ns, ns, alias)
				require_code_insertion_pos = 0
			v.insert(edit, require_code_insertion_pos, require_code)
			added_require_alias_end_pos = require_code_insertion_pos + len(require_code) - 3
		elif require_region.end() < 0:
			# 2-2. There is no ":require" in ns form
			require_code = "\n  (:require [{0} :as {1}])".format(ns, alias)
			require_code_insertion_pos = ns_and_the_1st_arg_region.end()
			v.insert(edit, require_code_insertion_pos, require_code)
			added_require_alias_end_pos = require_code_insertion_pos + len(require_code) - 2
		else:
			# 2-3. There is ":require" in ns form
			require_code = "\n            [{0} :as {1}]".format(ns, alias)
			require_code_insertion_pos = require_region.end() - 1
			v.insert(edit, require_code_insertion_pos, require_code)
			added_require_alias_end_pos = require_code_insertion_pos + len(require_code) - 1
		replaced_regions.append(sublime.Region(added_require_alias_end_pos - len(alias), added_require_alias_end_pos))

		# replace all of the inlines
		ns_regexp = ns.replace(".", "\.") # TODO: general and safe way to `string -> regexp` conversion
		cnt = len(v.find_all(ns_regexp)) - 1
		for i in range(cnt):
			region = v.find_all(ns_regexp)[1]
			v.replace(edit, region, alias)
			begin = region.begin()
			replaced_regions.append(sublime.Region(begin, begin + len(alias)))

		# select all the replaced
		sel = self.view.sel()
		sel.clear()
		sel.add_all(replaced_regions)
