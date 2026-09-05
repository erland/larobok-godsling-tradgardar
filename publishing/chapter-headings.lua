local chapter_pattern = "^Kapitel%s+(%d+):%s+(.+)$"

local function escape_latex(text)
  local replacements = {
    ["\\"] = "\\textbackslash{}", ["{"] = "\\{", ["}"] = "\\}",
    ["#"] = "\\#", ["$"] = "\\$", ["%"] = "\\%", ["&"] = "\\&",
    ["_"] = "\\_", ["^"] = "\\textasciicircum{}", ["~"] = "\\textasciitilde{}"
  }
  return (text:gsub("[\\{}#$%%&_%^~]", replacements))
end

function Header(el)
  if el.level ~= 1 then
    return nil
  end

  local text = pandoc.utils.stringify(el.content)

  if FORMAT:match("latex") and text == "Inledning" then
    return {
      pandoc.RawBlock("latex", "\\clearpage"),
      el
    }
  end

  local number, title = text:match(chapter_pattern)
  if not number then
    return nil
  end

  if FORMAT:match("latex") then
    local toc = escape_latex("Kapitel " .. number .. ": " .. title)
    local shown_title = escape_latex(title)
    local latex = table.concat({
      "\\clearpage",
      "\\phantomsection",
      "\\addcontentsline{toc}{section}{" .. toc .. "}",
      "\\begin{center}",
      "{\\Large Kapitel " .. number .. "}\\par",
      "\\vspace{0.35em}",
      "{\\Huge\\bfseries " .. shown_title .. "}\\par",
      "\\end{center}",
      "\\vspace{1.2em}"
    }, "\n")
    return pandoc.RawBlock("latex", latex)
  end

  local content = {
    pandoc.Span({pandoc.Str("Kapitel " .. number)}, pandoc.Attr("", {"chapter-number"})),
    pandoc.Span({pandoc.Str(": ")}, pandoc.Attr("", {"chapter-separator"})),
    pandoc.Span({pandoc.Str(title)}, pandoc.Attr("", {"chapter-title"}))
  }
  return pandoc.Header(1, content, el.attr)
end
