import sublime, sublime_plugin
import re

class ClojureInlineNamespaceRefactoringCommand(sublime_plugin.TextCommand):

	__clj_ns_char_regex = re.compile(r"[-.\w\d]")

	def extract_namespace_phrase_region_at(self, pos):
		_pos = (pos - 1) if self.view.substr(pos) == "/" else pos
		begin, end = _pos, _pos
		while True:
			if self.__class__.__clj_ns_char_regex.match(self.view.substr(begin)) == None:
				break
			begin -= 1
		while True:
			if self.__class__.__clj_ns_char_regex.match(self.view.substr(end)) == None:
				break
			end += 1
		return sublime.Region(begin + 1, end)


	def run(self, edit):
		print("ClojureNsExtractor called")
		v = self.view
		sel = self.view.sel()
		alias_text_regions = []

		# 1. get namespace text
		ns_region = self.extract_namespace_phrase_region_at(sel[0].begin())
		ns = v.substr(ns_region).strip().split("/")[0]
		if len(ns) == 0:
			sublime.error_message("No namespace phrase at current cursol position.")
			return
		ns_suffix = ns.split(".")[-1]
		ns_alias = ns_suffix
		print("[ns, suffix, alias = {0}, {1}, {2}]".format(ns, ns_suffix, ns_alias))

		# 2. insert "require" phrase in ns
		ns_and_the_1st_arg_region = v.find(r"\(ns[,\s]+[^,\s]+", 0)
		require_region = v.find(r"\(ns[,\s](.|\n)+\(:require[\s,][^)]+?\)", 0)
		print("require code region: " + str(require_region))
		if ns_and_the_1st_arg_region.end() < 0:
			# 2-1. There id no "ns" declaration
			end_of_shebang_or_dependencies_regions = v.find_all(r"^(#!.+|'\{:dependencies(.|\n)+?\})")
			if len(end_of_shebang_or_dependencies_regions) > 0:
				# 2-1-1. There are shebang or dependencies
				require_code = "\n\n(require '({0} :as {1}))\n".format(ns, ns_alias)
				require_code_insertion_pos = end_of_shebang_or_dependencies_regions[-1].end()
			else:
				# 2-1-2. There are not both shebang and dependencies
				require_code = "(require '({0} :as {1}))\n".format(ns, ns_alias)
				require_code_insertion_pos = 0
			v.insert(edit, require_code_insertion_pos, require_code)
			added_require_alias_end_pos = require_code_insertion_pos + len(require_code) - 3
		elif require_region.end() < 0:
			# 2-2. There is no ":require" in ns declaration
			require_code = "\n  (:require [{0} :as {1}])".format(ns, ns_alias)
			require_code_insertion_pos = ns_and_the_1st_arg_region.end()
			v.insert(edit, require_code_insertion_pos, require_code)
			added_require_alias_end_pos = require_code_insertion_pos + len(require_code) - 2
		else:
			# 2-3. There is ":require" in ns declaration
			require_code = "\n            [{0} :as {1}]".format(ns, ns_alias)
			require_code_insertion_pos = require_region.end() - 1
			v.insert(edit, require_code_insertion_pos, require_code)
			added_require_alias_end_pos = require_code_insertion_pos + len(require_code) - 1
		alias_text_regions.append(sublime.Region(added_require_alias_end_pos - len(ns_alias), added_require_alias_end_pos))

		# 3. replace all of the inline namespace
		ns_regexp = ns.replace(".", "\.") # TODO: general and safe way to `string -> regexp` conversion
		inline_ns_text_count = len(v.find_all(ns_regexp)) - 1
		for i in range(inline_ns_text_count):
			# TODO: finding in each loop is bad effect for performance.
			ns_regions = v.find_all(ns_regexp)
			inline_ns_region = ns_regions[1]
			v.replace(edit, inline_ns_region, ns_alias)
			begin = inline_ns_region.begin()
			alias_text_regions.append(sublime.Region(begin, begin + len(ns_alias)))

		# 4. select all the alias which is replaced
		sel.clear()
		sel.add_all(alias_text_regions)
		print("ClojureNsExtractor finished")
