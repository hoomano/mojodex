# Database

The Mojodex database is a PostgreSQL database using the pg_vector extension to store and query vector data.

The database is launched as a Docker container and is accessed by the `backend` and `background` services. See general documentation for more information.

## Database schema

You can have a look at the database schema at dbdiagram.io:
https://dbdiagram.io/d/MojodexDatabase-659d0645ac844320ae85b440

> Table names are prefixed with `md_` standing for "Mojodex".

## Initialization of Mojodex data

The `create-mojodex-data.sql` and `init-mojodex-data.sql` files respectively contains the SQL script to create the Mojodex schema and data. You can modify this file to add or remove data. For now, all updates are stacked in this file and no sql patch is provided.


## Entities
Each table is represented as a python class in `mojodex_code/entities/db_base_entities.py`. This file is generated using `sqlacodegen`tool:
```bash
sqlacodegen postgresql+psycopg2://$DBUSER:$DBPASS@localhost:5432/$DBNAME --outfile mojodex_core/entities/db_base_entities.py
```

⚠️  Be sure to install `sqlacodegen` with the appropriate pg_vector features:
```
python3 -m pip install git+https://github.com/hoomano/sqlacodegen.git@feature-pgvector
```

Some of those entities are then extended in `mojodex_code/entities/` to add specific methods or attributes. To get the most out of an entity in the code, retrieve it by querying then database using the aproppriate daughter class.

Example using `User` entity, daughter of base entity `MdUser`:
```
db_session.query(User).get(user_id)
```

You can also directly create object using the daughter class:
```
new_user = User(name="John Doe", email="john@doe.com")
db_session.add(new_user)
db_session.commit()
```