cwlVersion: v1.2
class: ExpressionTool
doc: |
  Selects the first input with a non-null value containing at least one
  non-null element.  Priority: input1 > input2 > input3.

inputs:
  input1: Any[]?
  input2: Any[]?
  input3: Any[]?

outputs:
  output: Any[]

expression: |
  ${
    var hasValue = function(arr) {
      return arr != null && arr.some(function(e) { return e != null; });
    };

    var result = null;
    if (hasValue(inputs.input1)) {
      result = inputs.input1;
    } else if (hasValue(inputs.input2)) {
      result = inputs.input2;
    } else if (hasValue(inputs.input3)) {
      result = inputs.input3;
    }

    return { "output": result };
  }

requirements:
  InlineJavascriptRequirement: {}
