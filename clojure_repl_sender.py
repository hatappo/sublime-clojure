import sublime, sublime_plugin

sublime.CLASS_WORD_START | sublime.CLASS_WORD_END

def cursol_symbol(v):
	pos = v.sel()[0].begin()
	cls = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
	r = v.expand_by_class(pos, cls, " ({[;")
	_r = v.find(r"[-/\w\d.]+[-\w\d]", r.begin())
	return v.substr(_r)

def cursol_block(v):
	# pos = v.sel()[0].begin()
	# cls = sublime.CLASS_PUNCTUATION_START | sublime.CLASS_PUNCTUATION_END
	strs = []
	v.run_command("expand_selection", {"to": "brackets"})
	v.run_command("expand_selection", {"to": "brackets"})
	for s in v.sel():
		strs.append(v.substr(s))
	return "\n\n".join(strs)

def repl_external_id(v):
	return v.scope_name(0).split(" ")[0].split(".", 1)[1] # may be "clojure"

def repl_send(v, text):
	external_id = repl_external_id(v)
	v.run_command("repl_send", {"external_id": external_id, "text": text})

class ClojureReplDocCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		v = self.view
		text = "(println) (clojure.repl/doc {})".format(cursol_symbol(v))
		repl_send(v, text)

class ClojureReplSourceCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		v = self.view
		text = "(println) (clojure.repl/source {})".format(cursol_symbol(v))
		repl_send(v, text)

class ClojureReplMacroexpand1Command(sublime_plugin.TextCommand):
	def run(self, edit):
		v = self.view
		text = "(println) (clojure.core/macroexpand-1 '{})".format(cursol_block(v))
		repl_send(v, text)

class ClojureReplMacroexpandCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		v = self.view
		text = "(println) (clojure.core/macroexpand '{})".format(cursol_block(v))
		repl_send(v, text)
