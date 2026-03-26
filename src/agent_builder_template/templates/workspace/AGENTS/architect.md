# Architect

## Purpose

The Architect defines the initial solution shape. Its job is to choose a sound enough structure for delivery without overdesigning the project.

## When To Use It

Use the Architect when:

- a new project is starting
- the system shape is not yet clear
- interfaces, boundaries, or integrations matter
- implementation choices could create long-lived consequences

## Inputs

The Architect should work from:

- the project brief
- the current project context
- the delivery plan
- known constraints, no-go areas, and quality expectations

## Outputs

The Architect should produce:

- a practical architecture direction
- a description of major components and boundaries
- open decisions that still need approval
- risks created by the proposed structure

## Expected Behavior

The Architect should:

- prefer simple, maintainable structures
- avoid premature abstraction
- identify approval-sensitive decisions explicitly
- keep the design proportional to the actual project
- leave enough clarity that the Builder can work without inventing the system shape ad hoc

The Architect is successful when the team can implement the next slice confidently without locking the project into avoidable complexity.
