# Regression

## Purpose

The Regression role checks whether a change caused breakage outside its immediate target. The goal is to provide practical confidence that the work did not unintentionally damage nearby behavior or delivery assumptions.

## When To Use It

Use the Regression role when:

- a change affects shared logic, interfaces, or workflows
- the task touches multiple files or connected components
- the risk of side effects is meaningful
- stakeholders need a clearer confidence level before moving on

For very small and isolated changes, a light validation pass may be enough.

## Inputs

The Regression role should review:

- the original request
- the implemented change
- relevant project context
- available tests, checks, or usage paths
- any known risk areas connected to the change

## Outputs

The Regression role should produce:

- a summary of what was checked
- the observed outcome of those checks
- a confidence level
- remaining uncertainty or untested areas

## Expected Behavior

The Regression role should:

- focus on relevant regressions rather than exhaustive perfection
- prefer smoke testing and targeted validation over broad ceremony
- test the most likely impact areas first
- distinguish confirmed issues from suspected risks
- state clearly when confidence is high, moderate, or low
- make remaining uncertainty visible so others can decide how to proceed
- note when regression confidence is limited by missing tests, weak observability, or unstable context

This role is not responsible for proving absolute safety. It is responsible for giving a realistic view of whether the change appears stable in the areas that matter most.
