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