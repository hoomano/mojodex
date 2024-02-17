# Create a new product

> Read [What's a product documentation](../../products/whats_a_product.md) before creating a new product.

## Creating a product category
- STEP 1: Create the json file
```
cp ./docs/configure_assistant/products/product_category_spec.json ./docs/configure_assistant/products/products_json/my_product_category.json
```
Fill the json values of my_product_category.json with the ones fitting your need for this product category.


- STEP 2: Add the product category to the database
Replace `<BACKOFFICE_SECRET>` with your actual token and run the following command in your terminal

```shell
curl -X 'PUT' \
  'http://localhost:5001/product_category' \
  -H 'Authorization: <BACKOFFICE_SECRET>' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d @./docs/configure_assistant/products/products_json/my_product_category.json
```

## Creating a product
- STEP 1: Create the json file
```
cp ./docs/configure_assistant/products/product_spec.json ./docs/configure_assistant/products/products_json/my_product.json
```

Fill the json values of my_product.json with the ones fitting your need for this product.

- STEP 2: Add the product to the database
Replace `<BACKOFFICE_SECRET>` and `<product_category_pk>` with the previously created category pk and run the following command in your terminal:

```shell
curl -X 'PUT' \
  'http://localhost:5001/product' \
    -H 'Authorization: <BACKOFFICE_SECRET>' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d @./docs/configure_assistant/products/products_json/my_product.json
```

> Remember a product category must have 1 free trial product (as defined in the [What's a product documentation](../../products/whats_a_product.md)). This product will be the one associated by default to users selecting the category at onboarding. If no free trial product is defined, the users will encounter an error at onboarding.

## Associating tasks to the product
Now that your product is created, you need to associate the tasks to the product. For each task you want to associate, run the following command in your terminal:
```shell
curl -X 'PUT' \
  'http://localhost:5001/product_task_association' \
  -H 'Authorization: <BACKOFFICE_SECRET>' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "datetime": "2024-02-14T11:00:00.000Z",
    "product_pk": <product_pk>,
    "task_pk": <task_pk>
}'
```

## Affecting the product to a user

### New user
A new user ccreating an account on Mojodex will go through an onboarding process. During this process, the user will be asked to select a product category. This category will define the user's profile and will automatically affect them the free trial product of this category.

### Existing user

#### Manually by an admin
An admin can affect a product to a user using the backoffice APIs. To do so, run the following command in your terminal:
```shell
curl -X 'PUT' \
  'http://localhost:5001/manual_purchase' \
  -H 'Authorization: <BACKOFFICE_SECRET>' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "datetime": "2024-02-14T11:53:58.771Z",
  "user_id": "<user_id>",
  "product_pk": <product_pk>,
  "custom_purchase_id": "string"
}'
```

> Remember, a user can't have 2 active subscriptions at the same time. If a user is affected with a new subscription, the previous one is automatically cancelled.

#### Buying a product using an implemented payment service
The user can also buy a product using Stripe or Apple in-app purchase flow, detailed in the [How it works documentation](../../products/how_it_works.md).


