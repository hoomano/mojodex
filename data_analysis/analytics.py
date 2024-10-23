import mojodex_core.entities.db_base_entities as dbe

import sqlalchemy as sa

from sqlalchemy.orm import Session
import pandas as pd


DBUSER = "assistant_db_user"
DBPASS = "password"
DBHOST = "mojodex_db"
DBNAME = "your_assistant_db"

connection_string = f"postgresql+psycopg2://{DBUSER}:{DBPASS}@{DBHOST}:5432/{DBNAME}"
engine = sa.create_engine(connection_string)

def full_table_subquery(session):
    # build the subquery first to select everything
    ute_query = sa.select(
        dbe.MdUser,
        dbe.MdUserTaskExecution,
        dbe.MdUserTask,
        dbe.MdTask,
        dbe.MdPurchase,
        dbe.MdProduct,
        dbe.MdProductCategory,
        dbe.MdUserWorkflowStepExecution,
        ).join(dbe.MdUserTask, dbe.MdUserTask.user_id == dbe.MdUser.user_id
        ).join(dbe.MdUserTaskExecution, dbe.MdUserTaskExecution.user_task_fk == dbe.MdUserTask.user_task_pk
        ).join(dbe.MdTask, dbe.MdTask.task_pk == dbe.MdUserTask.task_fk
        ).join(dbe.MdPurchase, dbe.MdPurchase.user_id == dbe.MdUser.user_id
        ).join(dbe.MdProduct, dbe.MdProduct.product_pk == dbe.MdPurchase.product_fk
        ).join(dbe.MdProductCategory, dbe.MdProductCategory.product_category_pk == dbe.MdProduct.product_category_fk
        ).outerjoin(dbe.MdUserWorkflowStepExecution, dbe.MdUserWorkflowStepExecution.user_task_execution_fk == dbe.MdUserTaskExecution.user_task_execution_pk
        ).filter(dbe.MdProduct.product_pk != 1)

    return ute_query.subquery()

def group_by_task_date_user(ute_subquery):
    unify_dates_subquery = sa.select(
        ute_subquery.c.user_task_execution_pk,
        ute_subquery.c.name.label('user'),
        ute_subquery.c.name_for_system.label('task_name'),
        sa.func.coalesce(ute_subquery.c.start_date, ute_subquery.c.creation_date).label('date')
        ).subquery()

    # extract year and month from the date
    query = sa.select(
        ##select the count in each group by
        unify_dates_subquery.c.user,
        unify_dates_subquery.c.task_name,
        sa.extract('year', unify_dates_subquery.c.date).label('year'),
        sa.extract('month', unify_dates_subquery.c.date).label('month'),
        sa.func.count(sa.distinct(unify_dates_subquery.c.user_task_execution_pk)).label('count_tasks'),
        ).group_by("task_name", "year", "month", "user")


    result = session.execute(query)

    return result.all()




with Session(engine) as session:
    ute_subquery = full_table_subquery(session)
    result = group_by_task_date_user(ute_subquery)

    # convert the result to a pandas dataframe

df = pd.DataFrame(result, columns=["user", "task_name", "year", "month", "count_tasks"])
df['year'] = df['year'].astype('Int64')
df['month'] = df['month'].astype('Int64')
# find rows with nan
nan_rows = df[df.isnull().any(axis=1)]
print(df.head())
# en lignes, les tâches Maya. En colonnes, les 6 derniers mois (inclure septembre). Dans les cellules : le nombre d'utilisateurs unique de chaque tâche chaque mois. Idéalement les tâches sont classées par ordre décroissant (en fonction du total d'user uniques, soit du total d'user uniques sur le dernier mois
# Onglet 1 : tableau avec les tâches et le nombre d'utilisateurs uniques de chaque tâche chaque mois

df_pivot = df.pivot_table(index="task_name", columns=["year", "month"], values="count_tasks", aggfunc="sum", fill_value=0)

# order df_pivot by the last column
df_pivot = df_pivot.sort_values(by=[df_pivot.columns[-1]], ascending=False)

# Onglet 2 : même tableau que dans l'onglet 1, mais au lieu de compter les unique users, on compte les occurences où la tâche a été utilisée (si le même user a utilisé la tâche 4 fois dans le mois, on compte 4)
df_pivot2 = df.pivot_table(index="task_name", columns=["year", "month"], values="user", aggfunc="count", fill_value=0)
df_pivot2 = df_pivot2.sort_values(by=[df_pivot2.columns[-1]], ascending=False)
# Onglet 3 à n : dans chaque onglet on fait un focus sur une tâche, en commençant par la première de la liste de l'onglet 1. Dans l'onglet de la tâche n, on a dans la 1e colonne les noms des utilisateurs et dans la 2e colonne le nombre de fois où ils ont utilisé la feature sur les 6 derniers mois (inclure septembre). Si facile, au lien de faire en 2 colonnes on fait un tableau comme dans les autres onglets où on a le détail mois par mois sur les 6 derniers mois

df_task_dict = {}
for task_name in df_pivot.index:
    df_task = df[df["task_name"] == task_name]
    df_task_pivot = df_task.pivot_table(index="user", columns=["year", "month"], values="count_tasks", aggfunc="sum", fill_value=0)

    df_task_pivot = df_task_pivot.sort_values(by=[df_task_pivot.columns[-1]], ascending=False)
    df_task_dict[task_name] = df_task_pivot


# write to excel
with pd.ExcelWriter(path="./output.xlsx") as writer:
    df_pivot.to_excel(writer, sheet_name="task_per_month")
    df_pivot2.to_excel(writer, sheet_name="unique_user_per_month")
    for task_name, df_task in df_task_dict.items():
        print(task_name)
        df_task.to_excel(writer, sheet_name=task_name[:30]) # limit to 30 characters for sheet name
