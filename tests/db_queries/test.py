

import itertools
import os
# env var
os.environ['DBHOST'] = 'localhost'
os.environ['DBNAME'] = 'your_assistant_db'
os.environ['DBUSER'] = 'assistant_db_user'
os.environ['DBPASS'] = 'password'

import pytz
from sqlalchemy import create_engine, func, extract, case, and_, over, desc, select, cast, or_, exists
from sqlalchemy.orm import sessionmaker, aliased
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql.functions import coalesce
from sqlalchemy.orm import object_session
# I want to import file that is ../../mojodex_core/entities.py relative to this file
import sys

sys.path.append("../../")
from mojodex_core.entities.db_base_entities import *
from mojodex_core.entities.user_workflow_execution import UserWorkflowExecution
from mojodex_core.entities.user_workflow_step_execution import UserWorkflowStepExecution
import json



# Replace this with your actual database URL
DATABASE_URL = f"postgresql+psycopg2://{os.environ['DBUSER']}:{os.environ['DBPASS']}@{os.environ['DBHOST']}:5432/{os.environ['DBNAME']}"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

current_step_in_validation = db.query(UserWorkflowStepExecution).get(3)
print(type(current_step_in_validation))
print(type(current_step_in_validation.workflow_step))

print(current_step_in_validation.workflow_step.definition_for_system)