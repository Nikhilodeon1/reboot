"""Build the single document a rater receives (standard library only).

    python v2/validation_kit/make_rater_docx.py OUTPUT.docx

It contains the instructions, the five questions of CARD.md, the three pinned cases of CASES.md, one answer table per case and a short
background section. It does not contain anything about what the authors expect.
"""
import sys
import zipfile
from xml.sax.saxutils import escape

CASES = [
    ("1", "Great Expectations", "version 1.25.0",
     "The column expectation expect_column_mean_to_be_between, run with the pandas execution engine. It returns a success flag.",
     "Official documentation: docs.greatexpectations.io. Source code: github.com/fivetran/great_expectations, tag 1.25.0."),
    ("2", "Deepchecks", "version 0.19.1",
     "The tabular train-test check on feature drift, FeatureDrift (older name TrainTestFeatureDrift), with its default condition add_condition_drift_score_less_than. The condition passes or fails.",
     "Official documentation: docs.deepchecks.com. Source code: github.com/deepchecks/deepchecks, tag 0.19.1."),
    ("3", "Evidently", "version 0.7.23",
     "The data drift check for one column (the ValueDrift metric, also used by DataDriftPreset), with its default statistical test and threshold. It reports whether drift was detected.",
     "Official documentation: docs.evidentlyai.com. Source code: github.com/evidentlyai/evidently, tag v0.7.23."),
]

ITEMS = [
    ("1_decidability", "1. Can it say \"I could not tell\"?",
     "When the statistic cannot be computed (an empty table, a column that is all missing values, a constant column, a single class), does the check say so, separately from a pass?",
     "yes = it reports undecidable, abstains, or raises an error. no = it returns a pass or a finite value with no warning. partly = it depends on the case (name the cases). unclear."),
    ("2_control_margins", "2. Controls and their distance from the threshold",
     "Does the documentation or output give a known-negative control for the check (a case that should not be flagged), and say how far its statistic lies from the threshold compared with how much the statistic varies from sample to sample?",
     "yes. control_only = a control is given but no distance. no. unclear."),
    ("3_uncertainty_at_operating_point", "3. Would the verdict change on another sample?",
     "Does the output or documentation say how likely the verdict is to change if the data were resampled at the sample size used (for example an interval, a p-value with a rule for reading it, or a probability of flagging)?",
     "yes. partly = an interval or p-value, but nothing about the verdict. no. unclear."),
    ("4_null_rate_and_nuisance_control", "4. False alarm rate and nuisance factors",
     "Does the documentation report how often the check flags when there is no effect, or give a control that holds a nuisance factor (for example sample size) fixed?",
     "yes. partly. no. unclear."),
    ("5_provenance_of_decision_rule", "5. Where does the threshold come from?",
     "Does the documentation say where the default threshold or rule comes from, and whether it was set before looking at data?",
     "yes = a derivation or a source is given. convention_only = stated as a default or a convention. no. unclear."),
]


def run(text, bold=False, size=None, color=None):
    props = ("<w:b/>" if bold else "") + (f'<w:color w:val="{color}"/>' if color else "") + (f'<w:sz w:val="{size}"/>' if size else "")
    return f"<w:r>{'<w:rPr>' + props + '</w:rPr>' if props else ''}<w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r>"


def para(text="", style=None, bold_lead=None, bold=False, size=None, keep=False, bullet=False):
    ppr = ""
    if style:
        ppr += f'<w:pStyle w:val="{style}"/>'
    if keep:
        ppr += "<w:keepNext/>"
    if bullet:
        ppr += '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
    body = (run(bold_lead, bold=True, size=size) if bold_lead else "") + (run(text, bold=bold, size=size) if text else "")
    return f"<w:p>{'<w:pPr>' + ppr + '</w:pPr>' if ppr else ''}{body}</w:p>"


def table(widths, rows, header=True):
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    borders = "".join(f'<w:{side} w:val="single" w:sz="6" w:space="0" w:color="808080"/>' for side in ("top", "left", "bottom", "right", "insideH", "insideV"))
    out = [f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:tblBorders>{borders}</w:tblBorders><w:tblLayout w:type="fixed"/>'
           '<w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/><w:bottom w:w="60" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar>'
           f"</w:tblPr><w:tblGrid>{grid}</w:tblGrid>"]
    for r_i, row in enumerate(rows):
        head = header and r_i == 0
        trpr = "<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>" if head else '<w:trPr><w:cantSplit/><w:trHeight w:val="900"/></w:trPr>'
        cells = []
        for w, text in zip(widths, row):
            shade = '<w:shd w:val="clear" w:color="auto" w:fill="D9E2F3"/>' if head else ""
            cells.append(f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shade}</w:tcPr>{para(text, style="Cell", bold=head)}</w:tc>')
        out.append(f"<w:tr>{trpr}{''.join(cells)}</w:tr>")
    out.append("</w:tbl>")
    return "".join(out)


def build_body():
    b = []
    b.append(para("Rating three data-checking tools", style="Title"))
    b.append(para("Thank you for helping. We want to know whether different people read a short five-question card the same way. You will rate three public Python libraries. There are no right answers that you are expected to guess, and disagreeing with us is useful. Plan about two hours."))
    b.append(para("Rules", style="Heading1"))
    for t in ["Work on your own.",
              "Use no AI tools at any step: no chatbots, no coding assistants, no AI search summaries, and no AI to tidy up your answers afterwards.",
              "Use the versions named below. If a documentation page describes a newer version, say so in the evidence box.",
              "Type your answers straight into the tables in this document.",
              "Do not write your name anywhere in the document.",
              "You may ask us what a question means. We cannot discuss which answer we would give."]:
        b.append(para(t, bullet=True))
    b.append(para("What is being rated", style="Heading1"))
    b.append(para("Each tool has a check that looks at data or a model and returns a verdict, such as pass or fail, or drift detected or not. The check computes a number (the statistic) and compares it with a rule (often a threshold). You answer the same five questions about each of the three checks. You may read the documentation and the source code. You do not have to run any code, and if you do, say so in the evidence box."))
    b.append(para("The five questions and their answer codes", style="Heading1"))
    for _, title, question, codes in ITEMS:
        b.append(para(title, style="Heading2"))
        b.append(para(question))
        b.append(para(codes, bold_lead="Codes: "))
    b.append(para("How to fill in a row", style="Heading2"))
    b.append(para("In the Answer box write one code, exactly as spelled above. In the Evidence box paste a link and the sentence or line of code you relied on. If you cannot tell, answer unclear and say where you looked. If you answer no because you found nothing, say where you looked."))
    for num, name, ver, what, where in CASES:
        b.append(para(f"Tool {num}: {name} ({ver})", style="Heading1", keep=True))
        b.append(para(what, bold_lead="Check: ", keep=True))
        b.append(para(where, bold_lead="Where to look: ", keep=True))
        rows = [["Row ID", "Question", "Answer", "Evidence (link and quoted line)"]]
        rows += [[f"{num}|{item}", title, "", ""] for item, title, _, _ in ITEMS]
        b.append(table([1900, 2600, 1500, 6960], rows))
    b.append(para("About you (no name)", style="Heading1", keep=True))
    rows = [["Question", "Your answer"]]
    rows += [[q, ""] for q in ["Years of Python experience", "Years of machine learning experience", "Had you used any of these three libraries before? Which?",
                               "About how long did this take?", "Did you use any AI tool at any step? If so, for what?",
                               "Did you run any code? If so, what?", "Have you helped with anything else for this project before? If so, what?",
                               "Anything about the questions that was unclear?"]]
    b.append(table([5200, 7760], rows))
    b.append(para("When you are done, save the document as a .docx file (from Google Docs: File, Download, Microsoft Word) and send it back."))
    return "".join(b)


NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'


def style(sid, name, size, bold=False, before=0, after=120, color=None, keep=False, outline=None):
    ppr = ("<w:keepNext/>" if keep else "") + f'<w:spacing w:before="{before}" w:after="{after}"/>' + (f'<w:outlineLvl w:val="{outline}"/>' if outline is not None else "")
    rpr = '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>' + ("<w:b/>" if bold else "") + (f'<w:color w:val="{color}"/>' if color else "") + f'<w:sz w:val="{size}"/>'
    default = ' w:default="1"' if sid == "Normal" else ""
    based = "" if sid == "Normal" else '<w:basedOn w:val="Normal"/>'
    return f'<w:style w:type="paragraph"{default} w:styleId="{sid}"><w:name w:val="{name}"/>{based}<w:qFormat/><w:pPr>{ppr}</w:pPr><w:rPr>{rpr}</w:rPr></w:style>'


def main(out):
    document = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:body>{build_body()}'
                '<w:sectPr><w:pgSz w:w="15840" w:h="12240" w:orient="landscape"/><w:pgMar w:top="1080" w:right="1440" w:bottom="1080" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>'
                "</w:body></w:document>")
    styles = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles {NS}>'
              + style("Normal", "Normal", 22) + style("Title", "Title", 36, bold=True, after=160, color="1F3864")
              + style("Heading1", "heading 1", 28, bold=True, before=240, after=120, color="1F3864", keep=True, outline=0)
              + style("Heading2", "heading 2", 23, bold=True, before=160, after=80, color="1F3864", keep=True, outline=1)
              + style("Cell", "Cell", 19, after=0) + "</w:styles>")
    numbering = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:numbering {NS}><w:abstractNum w:abstractNumId="0"><w:lvl w:ilvl="0"><w:start w:val="1"/>'
                 '<w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>'
                 '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num></w:numbering>')
    types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
             '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
             '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
             '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
    doc_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
                '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/></Relationships>')
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in [("[Content_Types].xml", types), ("_rels/.rels", rels), ("word/document.xml", document),
                           ("word/styles.xml", styles), ("word/numbering.xml", numbering), ("word/_rels/document.xml.rels", doc_rels)]:
            z.writestr(name, data.encode("utf-8"))
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1])
