# Create a new profile

> Read [What's a profile documentation](../../design-principles/profiles/whats_a_profile.md) before creating a new profile.

## Creating a profile category
- STEP 1: Create the json file
```
cp ./docs/guides/profiles/profile_category_spec.json ./docs/guides/profiles/profiles_json/my_profile_category.json
```
Fill the json values of my_profile_category.json with the ones fitting your need for this profile category.


- STEP 2: Add the profile category to the database
Replace `<BACKOFFICE_SECRET>` with your actual token and run the following command in your terminal

```shell
curl -X 'PUT' \
  'http://localhost:5001/profile_category' \
  -H 'Authorization: <BACKOFFICE_SECRET>' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d @./docs/guides/profiles/profiles_json/my_profile_category.json
```

## Creating a profile
- STEP 1: Create the json file
```
cp ./docs/guides/profiles/profile_spec.json ./docs/guides/profiles/profiles_json/my_profile.json
```

Fill the json values of my_profile.json with the ones fitting your need for this profile.

- STEP 2: Add the profile to the database
Replace `<BACKOFFICE_SECRET>` and `<profile_category_pk>` with the previously created category pk and run the following command in your terminal:

```shell
curl -X 'PUT' \
  'http://localhost:5001/profile' \
    -H 'Authorization: <BACKOFFICE_SECRET>' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d @./docs/guides/profiles/profiles_json/my_profile.json
```

## Associating tasks to the profile
Now that your profile is created, you need to associate the tasks to the profile. For each task you want to associate, run the following command in your terminal:
```shell
curl -X 'PUT' \
  'http://localhost:5001/profile_task_association' \
  -H 'Authorization: <BACKOFFICE_SECRET>' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "datetime": "2024-02-14T11:00:00.000Z",
    "profile_pk": <profile_pk>,
    "task_pk": <task_pk>
}'
```

## Affecting the profile to a user

#### Manually by an admin
An admin can affect a profile to a user using the backoffice APIs. To do so, run the following command in your terminal:
```shell
curl -X 'PUT' \
  'http://localhost:5001/manual_purchase' \
  -H 'Authorization: <BACKOFFICE_SECRET>' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "datetime": "2024-02-14T11:53:58.771Z",
  "user_id": "<user_id>",
  "profile_pk": <profile_pk>,
  "custom_purchase_id": "string"
}'
```
