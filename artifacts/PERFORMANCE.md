backend:
- transaction pooler to be used so single connection can be leveraged
- seed script runs in one transaction, so to avoid data collisions
- sort, filter etc are on db layer, so api do not load the table in python

database:
- indexes on the given filters: country, job_title, department, name and payrolls.month.
- unneeded fields were removed iteratively

frontend (this commit involves one)
- data is fetched on server components, off load from browser
- page skeleton is pre-rendered, only dynamic js is hydrated later
- nextjs caches are used on many components
- frontend validations before making a request
- cached the filter request because it does not change often