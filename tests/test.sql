-- all user_workflow_execution_step with creation date > 2h from now
SELECT * FROM md_user_workflow_execution_step WHERE creation_date < NOW() - INTERVAL '2 hours';