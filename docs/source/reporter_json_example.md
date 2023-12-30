# JSON Reporter Example Report

```json
{
  "mutant_trials": [
    {
      "mutant": {
        "mutator_name": "FuncCall",
        "lineno": 45,
        "col_offset": 40,
        "end_lineno": 45,
        "end_col_offset": 73,
        "text": "None",
        "source_folder": "src",
        "source_file": "src/poodle/core.py",
        "unified_diff": "--- src/poodle/core.py\n+++ [Mutant] src/poodle/core.py:45\n@@ -42,7 +42,7 @@\n         results = run_mutant_trails(work, mutants, timeout)\n \n         for trial in results.mutant_trials:\n-            trial.mutant.unified_diff = create_unified_diff(trial.mutant)\n+            trial.mutant.unified_diff = None\n \n         for reporter in work.reporters:\n             reporter(config=config, echo=work.echo, testing_results=results)\n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 2.0598676204681396
    },
    {
      "mutant": {
        "mutator_name": "Number",
        "lineno": 186,
        "col_offset": 43,
        "end_lineno": 186,
        "end_col_offset": 44,
        "text": "-1",
        "source_folder": "src",
        "source_file": "src/poodle/mutate.py",
        "unified_diff": "--- src/poodle/mutate.py\n+++ [Mutant] src/poodle/mutate.py:186\n@@ -183,7 +183,7 @@\n             add_line_filter(line_filters, lineno, \"all\")\n         no_mut_filter: list[str] = re.findall(r\"#\\s*nomut:?\\s*([A-Za-z0-9,\\s]*)[#$]*\", line)\n \n-        if no_mut_filter and no_mut_filter[0].strip().lower() in (\"start\", \"on\"):\n+        if no_mut_filter and no_mut_filter[-1].strip().lower() in (\"start\", \"on\"):\n             no_mut_on = True\n \n         if no_mut_on:\n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 2.5591189861297607
    },
    {
      "mutant": {
        "mutator_name": "Number",
        "lineno": 196,
        "col_offset": 43,
        "end_lineno": 196,
        "end_col_offset": 44,
        "text": "-1",
        "source_folder": "src",
        "source_file": "src/poodle/mutate.py",
        "unified_diff": "--- src/poodle/mutate.py\n+++ [Mutant] src/poodle/mutate.py:196\n@@ -193,7 +193,7 @@\n                 for mutator in mutators.split(\",\"):\n                     add_line_filter(line_filters, lineno, mutator.strip())\n \n-        if no_mut_filter and no_mut_filter[0].strip().lower() in (\"end\", \"off\"):\n+        if no_mut_filter and no_mut_filter[-1].strip().lower() in (\"end\", \"off\"):\n             no_mut_on = False\n \n     return line_filters\n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 2.464325428009033
    },
    {
      "mutant": {
        "mutator_name": "Keyword",
        "lineno": 108,
        "col_offset": 79,
        "end_lineno": 108,
        "end_col_offset": 83,
        "text": "False",
        "source_folder": "src",
        "source_file": "src/poodle/util.py",
        "unified_diff": "--- src/poodle/util.py\n+++ [Mutant] src/poodle/util.py:108\n@@ -105,7 +105,7 @@\n def create_unified_diff(mutant: Mutant) -> str | None:\n     \"\"\"Add unified diff to mutant.\"\"\"\n     if mutant.source_file:\n-        file_lines = mutant.source_file.read_text(\"utf-8\").splitlines(keepends=True)\n+        file_lines = mutant.source_file.read_text(\"utf-8\").splitlines(keepends=False)\n         file_name = str(mutant.source_file)\n         return \"\".join(\n             difflib.unified_diff(\n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 3.1800050735473633
    },
    {
      "mutant": {
        "mutator_name": "String",
        "lineno": 108,
        "col_offset": 50,
        "end_lineno": 108,
        "end_col_offset": 57,
        "text": "'XXutf-8XX'",
        "source_folder": "src",
        "source_file": "src/poodle/util.py",
        "unified_diff": "--- src/poodle/util.py\n+++ [Mutant] src/poodle/util.py:108\n@@ -105,7 +105,7 @@\n def create_unified_diff(mutant: Mutant) -> str | None:\n     \"\"\"Add unified diff to mutant.\"\"\"\n     if mutant.source_file:\n-        file_lines = mutant.source_file.read_text(\"utf-8\").splitlines(keepends=True)\n+        file_lines = mutant.source_file.read_text('XXutf-8XX').splitlines(keepends=True)\n         file_name = str(mutant.source_file)\n         return \"\".join(\n             difflib.unified_diff(\n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 1.995598316192627
    },
    {
      "mutant": {
        "mutator_name": "Compare",
        "lineno": 26,
        "col_offset": 7,
        "end_lineno": 26,
        "end_col_offset": 25,
        "text": "summary.trials <= 1",
        "source_folder": "src",
        "source_file": "src/poodle/reporters/basic.py",
        "unified_diff": "--- src/poodle/reporters/basic.py\n+++ [Mutant] src/poodle/reporters/basic.py:26\n@@ -23,7 +23,7 @@\n     \"\"\"Echo quick summary to console.\"\"\"\n     echo(\"\")\n     summary = testing_results.summary\n-    if summary.trials < 1:\n+    if summary.trials <= 1:\n         echo(\"!!! No mutants found to test !!!\", fg=\"yellow\")\n         return\n \n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 2.012969493865967
    },
    {
      "mutant": {
        "mutator_name": "Compare",
        "lineno": 49,
        "col_offset": 12,
        "end_lineno": 49,
        "end_col_offset": 47,
        "text": "str(trial.mutant.source_file) and ''",
        "source_folder": "src",
        "source_file": "src/poodle/reporters/basic.py",
        "unified_diff": "--- src/poodle/reporters/basic.py\n+++ [Mutant] src/poodle/reporters/basic.py:49\n@@ -46,7 +46,7 @@\n     failed_trials.sort(\n         key=lambda trial: (\n             trial.mutant.source_folder,\n-            str(trial.mutant.source_file) or \"\",\n+            str(trial.mutant.source_file) and '',\n             trial.mutant.lineno,\n             trial.mutant.mutator_name,\n         )\n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 3.1697938442230225
    },
    {
      "mutant": {
        "mutator_name": "Number",
        "lineno": 26,
        "col_offset": 24,
        "end_lineno": 26,
        "end_col_offset": 25,
        "text": "2",
        "source_folder": "src",
        "source_file": "src/poodle/reporters/basic.py",
        "unified_diff": "--- src/poodle/reporters/basic.py\n+++ [Mutant] src/poodle/reporters/basic.py:26\n@@ -23,7 +23,7 @@\n     \"\"\"Echo quick summary to console.\"\"\"\n     echo(\"\")\n     summary = testing_results.summary\n-    if summary.trials < 1:\n+    if summary.trials < 2:\n         echo(\"!!! No mutants found to test !!!\", fg=\"yellow\")\n         return\n \n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 2.3608908653259277
    },
    {
      "mutant": {
        "mutator_name": "String",
        "lineno": 49,
        "col_offset": 45,
        "end_lineno": 49,
        "end_col_offset": 47,
        "text": "'XXXX'",
        "source_folder": "src",
        "source_file": "src/poodle/reporters/basic.py",
        "unified_diff": "--- src/poodle/reporters/basic.py\n+++ [Mutant] src/poodle/reporters/basic.py:49\n@@ -46,7 +46,7 @@\n     failed_trials.sort(\n         key=lambda trial: (\n             trial.mutant.source_folder,\n-            str(trial.mutant.source_file) or \"\",\n+            str(trial.mutant.source_file) or 'XXXX',\n             trial.mutant.lineno,\n             trial.mutant.mutator_name,\n         )\n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 3.2349610328674316
    },
    {
      "mutant": {
        "mutator_name": "String",
        "lineno": 22,
        "col_offset": 42,
        "end_lineno": 22,
        "end_col_offset": 53,
        "text": "'XXtemplatesXX'",
        "source_folder": "src",
        "source_file": "src/poodle/reporters/html.py",
        "unified_diff": "--- src/poodle/reporters/html.py\n+++ [Mutant] src/poodle/reporters/html.py:22\n@@ -19,7 +19,7 @@\n \n def template_path() -> Path:\n     \"\"\"Return the path to the HTML Template folder.\"\"\"\n-    return Path(__file__).parent.parent / \"templates\"\n+    return Path(__file__).parent.parent / 'XXtemplatesXX'\n \n \n STATIC_FILES = [\n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 2.860416889190674
    },
    {
      "mutant": {
        "mutator_name": "Compare",
        "lineno": 90,
        "col_offset": 11,
        "end_lineno": 90,
        "end_col_offset": 64,
        "text": "'source_file' in d or d['source_folder'] is not None",
        "source_folder": "src",
        "source_file": "src/poodle/data_types/data.py",
        "unified_diff": "--- src/poodle/data_types/data.py\n+++ [Mutant] src/poodle/data_types/data.py:90\n@@ -87,7 +87,7 @@\n         \"\"\"Correct fields in Dictionary for JSON deserialization.\"\"\"\n         if \"source_folder\" in d:\n             d[\"source_folder\"] = Path(d[\"source_folder\"])\n-        if \"source_file\" in d and d[\"source_folder\"] is not None:\n+        if 'source_file' in d or d['source_folder'] is not None:\n             d[\"source_file\"] = Path(d[\"source_file\"])\n         return d\n \n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 2.748727321624756
    },
    {
      "mutant": {
        "mutator_name": "Keyword",
        "lineno": 83,
        "col_offset": 31,
        "end_lineno": 83,
        "end_col_offset": 35,
        "text": "' '",
        "source_folder": "src",
        "source_file": "src/poodle/data_types/data.py",
        "unified_diff": "--- src/poodle/data_types/data.py\n+++ [Mutant] src/poodle/data_types/data.py:83\n@@ -80,7 +80,7 @@\n \n     source_folder: Path\n     source_file: Path | None\n-    unified_diff: str | None = None\n+    unified_diff: str | None = ' '\n \n     @staticmethod\n     def from_dict(d: dict[str, Any]) -> dict[str, Any]:\n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 2.005250930786133
    },
    {
      "mutant": {
        "mutator_name": "Keyword",
        "lineno": 90,
        "col_offset": 60,
        "end_lineno": 90,
        "end_col_offset": 64,
        "text": "' '",
        "source_folder": "src",
        "source_file": "src/poodle/data_types/data.py",
        "unified_diff": "--- src/poodle/data_types/data.py\n+++ [Mutant] src/poodle/data_types/data.py:90\n@@ -87,7 +87,7 @@\n         \"\"\"Correct fields in Dictionary for JSON deserialization.\"\"\"\n         if \"source_folder\" in d:\n             d[\"source_folder\"] = Path(d[\"source_folder\"])\n-        if \"source_file\" in d and d[\"source_folder\"] is not None:\n+        if \"source_file\" in d and d[\"source_folder\"] is not ' ':\n             d[\"source_file\"] = Path(d[\"source_file\"])\n         return d\n \n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 3.1990931034088135
    },
    {
      "mutant": {
        "mutator_name": "Keyword",
        "lineno": 186,
        "col_offset": 30,
        "end_lineno": 186,
        "end_col_offset": 34,
        "text": "' '",
        "source_folder": "src",
        "source_file": "src/poodle/data_types/data.py",
        "unified_diff": "--- src/poodle/data_types/data.py\n+++ [Mutant] src/poodle/data_types/data.py:186\n@@ -183,7 +183,7 @@\n     @staticmethod\n     def from_dict(d: dict[str, Any]) -> dict[str, Any]:\n         \"\"\"Correct fields in Dictionary for JSON deserialization.\"\"\"\n-        d.pop(\"success_rate\", None)\n+        d.pop(\"success_rate\", ' ')\n         d.pop(\"coverage_display\", None)\n         return d\n \n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 2.261491537094116
    },
    {
      "mutant": {
        "mutator_name": "Keyword",
        "lineno": 187,
        "col_offset": 34,
        "end_lineno": 187,
        "end_col_offset": 38,
        "text": "' '",
        "source_folder": "src",
        "source_file": "src/poodle/data_types/data.py",
        "unified_diff": "--- src/poodle/data_types/data.py\n+++ [Mutant] src/poodle/data_types/data.py:187\n@@ -184,7 +184,7 @@\n     def from_dict(d: dict[str, Any]) -> dict[str, Any]:\n         \"\"\"Correct fields in Dictionary for JSON deserialization.\"\"\"\n         d.pop(\"success_rate\", None)\n-        d.pop(\"coverage_display\", None)\n+        d.pop(\"coverage_display\", ' ')\n         return d\n \n     def to_dict(self) -> dict[str, Any]:\n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 2.5057268142700195
    },
    {
      "mutant": {
        "mutator_name": "Number",
        "lineno": 157,
        "col_offset": 25,
        "end_lineno": 157,
        "end_col_offset": 26,
        "text": "1",
        "source_folder": "src",
        "source_file": "src/poodle/data_types/data.py",
        "unified_diff": "--- src/poodle/data_types/data.py\n+++ [Mutant] src/poodle/data_types/data.py:157\n@@ -154,7 +154,7 @@\n     @property\n     def success_rate(self) -> float:\n         \"\"\"Return the success rate of the test run.\"\"\"\n-        if self.trials > 0:\n+        if self.trials > 1:\n             return self.found / self.trials\n         if self.tested > 0:\n             return self.found / self.tested\n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 2.6431467533111572
    },
    {
      "mutant": {
        "mutator_name": "Number",
        "lineno": 159,
        "col_offset": 25,
        "end_lineno": 159,
        "end_col_offset": 26,
        "text": "1",
        "source_folder": "src",
        "source_file": "src/poodle/data_types/data.py",
        "unified_diff": "--- src/poodle/data_types/data.py\n+++ [Mutant] src/poodle/data_types/data.py:159\n@@ -156,7 +156,7 @@\n         \"\"\"Return the success rate of the test run.\"\"\"\n         if self.trials > 0:\n             return self.found / self.trials\n-        if self.tested > 0:\n+        if self.tested > 1:\n             return self.found / self.tested\n         return 0.0\n \n"
      },
      "result": {
        "found": false,
        "reason_code": "Mutant Not Found",
        "reason_desc": null
      },
      "duration": 2.8689138889312744
    }
  ],
  "summary": {
    "trials": 1323,
    "tested": 1323,
    "found": 1306,
    "not_found": 17,
    "timeout": 0,
    "errors": 0,
    "success_rate": 0.9871504157218443,
    "coverage_display": "98.72%"
  }
}
```