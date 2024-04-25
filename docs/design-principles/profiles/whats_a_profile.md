# What is a profile?

Profile concept is used in Mojodex to define a group of users depending on their needs. Profiles and roles are ways to provide each user with a personalized, adapted experience on Mojodex.

## Profile VS Product
The concept of profile has been introduced after notion of product. A profile and a product point exactly to the same object in database.
A profile/role is just a vocabulary that matches better to a "pre-set" user configuration versus a product/purchase the user would buy on itself.
A profile is generally pre-configured by an admin and assigned to a user through a role.

## Main concepts

### Profile
The profile concepts are the same as the product concepts, knowing that:
- a profile's "free" status is always true
- a profile's n_tasks and days_validity limits are always null
- product_stripe_id and product_apple_id are always null

Finally, variables of a profile are:

- a **label** to identify it
- some **display data** to display on the user's interface in their language (name of the profile)
- a **status** (active or inactive)
- a **profile_category** to which it belongs

### Profile Task
As profile_task defines a set of tasks the user can execute on Mojodex. A profile task is a task that is part of a profile. Those associations are stored in the dedicated DB table `md_product_task`.

### Profile category
A profile category is a category of profile. It is used to group profiles together.
A profile category has:
- a **label** to identify it
- an **emoji** to display on the user's interface
- some **display data** to display on the user's interface in their language (name and description)
- a **visible** boolean status : flag to indicate if it's visible or not from the user's interface at the time to choose a category if onboarding is done by user.
- an **implicit goal**: This goal will be affected to the user account as their initial goal. This goal is then used in the assistant's prompt to drive the assistance by this goal.


### Role
A role is the relation between a user and a profile. It is the equivalent to a purchase when speaking about products. It is created when a profile is affected to a user.

### User Task
When a new role is created (e.g. a profile is affected to a user), the user is granted access to the tasks of the profile. This creates an association between the user and each task of the profile. This association is stored in the dedicated DB table `md_user_task`.
