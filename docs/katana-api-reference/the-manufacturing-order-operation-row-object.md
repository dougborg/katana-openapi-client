# The manufacturing order operation row object

Attribute Description id Unique identifier for the object. status Status of the
operation. Possible values are “NOT_STARTED”, “BLOCKED”, "IN_PROGRESS", "PAUSED", and
“COMPLETED”. rank A numerical value used for ranking the operations. We use an internal
numeration system where values are not sequential. Operations with a higher value are
ranked first. manufacturing_order_id The ID of the manufacturing order the operation row
belongs to. operation_id The ID of the operation needed to perform to make the product
on the manufacturing order. operation_name The name of the operation needed to perform
to make the product on the manufacturing order. resource_id The ID of the workstation or
a person required for completing a certain operation. resource_name The name of the
workstation or a person required for completing a certain operation. assigned_operators
An array of operators assigned to the task. assigned_operators.operator_id The ID of the
operator assigned to the task. assigned_operators.name The name of the operator assigned
to the task. assigned_operators.deleted_at The timestamp when the operator object was
deleted. completed_by_operators An array of operators who completed the task.
completed_by_operators.operator_id The ID of the operator who completed the task.
completed_by_operators.name The name of the operator who completed the task.
completed_by_operators.deleted_at The timestamp when the operator object was deleted.
active_operator_id The ID of the operator who is active on the task. type Different
operation types allow you to use different cost calculations depending on the type of
product operation process : The process operation type is best for when products are
individually built and time is the main driver of cost. setup : The setup operation type
is best for setting up a machine for production where the production quantity doesn't
affect cost. perUnit : The per unit operation type is best when cost of time isn't a
factor, but only the quantity of product made. fixed : The fixed cost operation type is
useful for adding the expected extra costs that go into producing a product.
planned_time_per_unit (deprecated) (This field is deprecated in favor of
planned_time_parameter) The planned duration of an operation, in seconds, to either
manufacture one unit of a product or complete a manufacturing order (based on type).
planned_time_parameter The planned duration of an operation, in seconds, to either
manufacture one unit of a product or complete a manufacturing order (based on type).
total_actual_time The total actual time for completing the manufacturing order operation
measured in seconds. planned_cost_per_unit The expected cost of an operation per unit of
product, calculated by the system. total_actual_cost The total actual cost of this
operation step for making the inserted amount of products. total_actual_cost =
cost_per_hour * (total_actual_time / 3600). cost_per_hour (deprecated) (This field is
deprecated in favor of cost_parameter) The expected cost of an operation, either total
or per hour/unit of product (based on type). Total cost of the operation on a
manufacturing order is calculated as follows: process : cost = cost_parameter x
planned_time_parameter (in hours) x product quantity setup : cost = cost_parameter x
planned_time_parameter (in hours) perUnit : cost = cost_parameter x product quantity
fixed : cost = cost_parameter cost_parameter The expected cost of an operation, either
total or per hour/unit of product (based on type). Total cost of the operation on a
manufacturing order is calculated as follows: process : cost = cost_parameter x
planned_time_parameter (in hours) x product quantity setup : cost = cost_parameter x
planned_time_parameter (in hours) perUnit : cost = cost_parameter x product quantity
fixed : cost = cost_parameter group_boundary A numerical value that is used to group
manufacturing operations that are to be performed in parallel order.
is_status_actionable A boolean value that is used to determine if an operation status
can be changed or not. Operations that have is_status_actionable equal to false, their
status can not be changed. completed_at The timestamp when the operation was completed.
created_at The timestamp when the manufacturing order recipe row was created. updated_at
The timestamp when the manufacturing order recipe row was last updated. deleted_at The
timestamp when the manufacturing order recipe row was deleted.
