# hand written doc, used for maintaining append only key decisions, made in order.

**Initial Planning**

tech stack - nextjs, fastapi, psql

functional requirements
 - configurable dashboard (shadcn ui for simplicity, chart to show month's data)
 - Filters (default filter in view -> month) to be run on server
    id
    name
    country
    salary


non-functional requirements
 - accesibility
 - pagination
 - validation on both frontend/backend layer


CORE DATA MODEL
    
    EMPLOYEES
        - id, name, email, monthly_salary, country, department, is_active, timestamps, last_transaction_at

    PAYROLLS
        -id, employee_id(fk), month, base, bonus, esops, currency, payment_method, timestamps
        - UNIQUE (employee_id, month) 
    

left out things:
 - authentication (assuming this portal is for one HR, auth would add extra step and complexity)
 - dedicated cache like redis (some caching would be on client side, dont wanna overengineer and overcomplicate)
 - redux or any central store, would be good to use if we want to cache search results, or when we introduce more search options

 updated 
 - dropped the salary filter, as multiple currencies would needed to be bound with it, for sake of simplicity
 - added a job title field, for better comparisons and filters
 - last_transaction_at field dropped, as it was bringing redundancy
 - payment methods reduced to 2 values -> bank, wallet
 - updated tests and diagrams


API model schema (proper versioning and prefixed and propely validated)
 - ALL payrolls by month
    GET /month?filter_query_params (paginated list, probably a JOIN in the backend)
    GET /insights (doubtful if i should include this, or unecessary overhead)
 - EMPLOYEE
    - GET /employees/:id
    - PATCH /employees/:id
    - DELETE /employees/:id (set is_active to false, not actual delete)
    - POST /employees
 - PAYROLL
    - GET /payrolls/:id
    - PATCH /payrolls/:id
    - POST /payrolls

POINTS:
    - maintain historic data, set active to false if someone resigns, payrolls indicate transactions so shouldnt be allowed to delete
    - dashboard chart to show "paid vs total employees for the month"


NEXT STEPS and frontend views planning:
    ASKED claude to review the model, it suggested some good changes missed by me which i approved, and some complex ones which i disapproved.
    - it suggested sorting salaries, fixed date format, DELETE TO PATCH
    - suggested some changes in /month api, which merged employees with /month api with some filters

    NEW model looks like
    /api/v1
    GET   /employees?month=&id=&name=&country=&job_title= (paginated)
    POST  /employees
    GET   /employees/{id}
    PATCH /employees/{id}                     
    POST  /employees/{id}/payrolls

    GET   /payrolls/{id}
    PATCH /payrolls/{id}
    GET   /insights/payroll-status?month=&country=    (chart)
    GET   /insights/pay-by-job-title?country=

    GET   /filters

    frontend 
    - / -> dashboard
    - /insights
    - /employees , /employees/new, /employees/:id
    - /payrolls/id

    error page and handling


revamp ui/ux and search filters

its about time i shall add org level simple stateless auth, for simplicity going with email password token based auth while maitaining basic security

 - login with JWT, TTL 8 hours, frontend keeps it in an HttpOnly cookie
 - logout: users.session_version is copied into every token, logout changes it so all earlier tokens stop working
 - organizations table, users and employees belong to one organization, another organization's records give 404

 - demo login is seeded within script

some left out decisions
-  user management ui and roles(role based access control), password reset, refresh tokens, limiting login attempts