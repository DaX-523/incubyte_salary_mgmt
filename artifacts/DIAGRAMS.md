# Diagrams

Derived from `REQUIREMENTS.md` (up to "org level simple stateless auth") and the code as built,
including what was added after review: pay by country and average salaries, payroll history, the
CSV export, and no payrolls before the month an employee joined. Deactivation stays
`DELETE /employees/{id}`, which sets `is_active` to false. `init.png` adds server-side pagination.

## Core data model

Every query is limited to the logged-in user's organization. Payrolls reach their organization
through the employee, so the fact is stored once.

```mermaid
erDiagram
    ORGANIZATIONS ||--o{ USERS : "has logins"
    ORGANIZATIONS ||--o{ EMPLOYEES : "employs"
    EMPLOYEES ||--o{ PAYROLLS : "is paid through"

    ORGANIZATIONS {
        int id PK
        string name UK "ACME"
        timestamp created_at
        timestamp updated_at
    }

    USERS {
        int id PK
        int organization_id FK "sees only this organization"
        string email UK "lowercase; used to log in"
        string name
        string password_hash "Argon2id, never the password"
        int session_version "copied into every token; logout adds 1"
        timestamp created_at
        timestamp updated_at
    }

    EMPLOYEES {
        int id PK
        int organization_id FK
        string name "search, sort"
        string email "search; unique within the organization, lowercase"
        decimal monthly_salary "local currency of country; sortable within a country"
        string country "filter; fixed once set; decides the currency"
        string department "derived from job_title"
        string job_title "filter; from a fixed list"
        boolean is_active "false = deactivated, never deleted"
        timestamp created_at "the joining month (UTC): first month on the books, first payable"
        timestamp updated_at
    }

    PAYROLLS {
        int id PK
        int employee_id FK "unique with month; fixed once set"
        date month "unique with employee_id; fixed once set"
        decimal base "amount paid, so a later raise doesn't change it"
        decimal bonus
        decimal esops
        string currency "set by the server from country"
        string payment_method "bank_transfer or digital_wallet"
        timestamp created_at
        timestamp updated_at
    }
```

## API (`/api/v1`)

```mermaid
flowchart LR
    subgraph auth["Auth"]
        login["POST /auth/login (public)<br/>email + password → JWT, 8 hours"]
        logout["POST /auth/logout<br/>session_version + 1: every earlier token stops working"]
        me["GET /auth/me<br/>name, email, organization"]
    end

    subgraph employees["Employees (login required)"]
        list["GET /employees<br/>month (required), name, email, country, job_title,<br/>sort_by name or monthly_salary (needs country),<br/>sort_order, page, page_size<br/>each row: employee + that month's payroll or null"]
        create["POST /employees<br/>department and currency derived"]
        read["GET /employees/{id}"]
        update["PATCH /employees/{id}<br/>country cannot change"]
        deactivate["DELETE /employees/{id}<br/>sets is_active to false"]
        exportCsv["GET /employees/export<br/>the list's filters and sort, every page, as CSV<br/>cells starting with = + - @ get a leading '"]
        history["GET /employees/{id}/payrolls<br/>pay history, newest month first"]
        pay["POST /employees/{id}/payrolls<br/>currency from country<br/>not before the month the employee joined"]
    end

    subgraph payrolls["Payrolls (login required)"]
        payroll["GET /payrolls/{id}"]
        correct["PATCH /payrolls/{id}<br/>amounts and method only"]
    end

    subgraph insights["Insights (login required)"]
        status["GET /insights/payroll-status<br/>month, country, job_title<br/>paid vs total (chart)"]
        byCountry["GET /insights/pay-by-country<br/>per country: headcount, average, total monthly salaries<br/>each in its own currency, never added across countries"]
        byTitle["GET /insights/pay-by-job-title<br/>country (required)<br/>headcount, lowest, average, highest"]
    end

    filters["GET /filters (public)<br/>countries, job titles, payment methods"]

    errors["Errors: 401 not logged in, wrong password, session ended ·<br/>404 not found or another organization's record ·<br/>409 duplicate email, duplicate month, inactive employee, month before joining ·<br/>422 invalid input"]

    style errors stroke-dasharray: 5 5
```

## Login and logout

```mermaid
sequenceDiagram
    actor hr as HR user
    participant web as Next.js server
    participant api as FastAPI
    participant db as PostgreSQL

    hr->>web: open /insights without a session cookie
    web-->>hr: proxy.ts redirects to /login
    hr->>web: email + password (server action)
    web->>api: POST /auth/login
    api->>db: user by email
    api->>api: check the Argon2 hash
    api-->>web: JWT with user id, session_version, expiry in 8 hours
    web-->>hr: session cookie (HttpOnly, SameSite=Lax, Secure), redirect to /
    hr->>web: open / with the cookie
    web->>api: GET /employees with Authorization Bearer token
    api->>db: user by id, token version must equal session_version
    api->>db: employees of the user's organization only
    api-->>web: page of employees
    web-->>hr: rendered dashboard
    hr->>web: Log out
    web->>api: POST /auth/logout
    api->>db: session_version + 1
    web-->>hr: cookie deleted, redirect to /login
    note over web,api: Any 401 later (expired or old token) redirects to /login
```

## CSV export

The browser only talks to the frontend, so the download goes through a route handler that adds
the token, the same way pages fetch data.

```mermaid
sequenceDiagram
    actor hr as HR user
    participant web as Next.js server
    participant api as FastAPI
    participant db as PostgreSQL

    hr->>web: Download CSV (link with the dashboard's month, filters and sort)
    web->>web: parse the query like the dashboard, drop page and page size
    web->>api: GET /employees/export with Authorization Bearer token
    api->>db: same query as the list, without LIMIT and OFFSET
    api->>api: write CSV, amounts as plain numbers, formula-like text prefixed with '
    api-->>web: text/csv
    web-->>hr: employees-YYYY-MM.csv (Content-Disposition: attachment)
```

## Requirements across the stack

```mermaid
flowchart LR
    hr(["HR user"])

    subgraph fe["Frontend (Next.js, shadcn/ui)"]
        proxy["proxy.ts<br/>no session cookie → /login"]
        loginPage["Login /login<br/>token kept in an HttpOnly cookie"]
        dash["Dashboard /<br/>month (default: current) + filters<br/>paid vs total chart, paginated table"]
        exportRoute["/employees/export<br/>CSV of the dashboard's list, every page"]
        insightsPage["Pay insights /insights<br/>by country, then by job title in one country"]
        employeePages["/employees/new, /employees/:id<br/>add, edit, payroll history, record payroll, deactivate"]
        payrollPage["/payrolls/:id<br/>correct a payroll"]
        feval["Form validation<br/>(browser + server actions)"]
        errorPage["Error, loading and not-found pages"]
    end

    subgraph be["Backend (FastAPI)"]
        authCheck["Login and token check<br/>JWT signature, expiry, session_version"]
        beval["Validation (Pydantic)"]
        services["Business rules<br/>derive department and currency,<br/>no payroll for inactive employees or before joining,<br/>averages rounded half up to the cent"]
        query["Filtering, sorting and pagination<br/>run in SQL, limited to the user's organization"]
    end

    subgraph data["PostgreSQL"]
        org[("ORGANIZATIONS")]
        users[("USERS")]
        emp[("EMPLOYEES")]
        pay[("PAYROLLS<br/>unique per employee + month")]
    end

    out["Left out on purpose:<br/>roles and user management, password reset,<br/>refresh tokens, limiting login attempts,<br/>dedicated cache (Redis), CSV import,<br/>salary change history"]

    hr --> proxy --> loginPage
    loginPage -- "POST /auth/login" --> authCheck
    proxy --> dash
    hr --> insightsPage
    insightsPage -- "rank a job title by salary" --> dash
    dash --> employeePages --> payrollPage
    dash -- "Download CSV" --> exportRoute
    employeePages --> feval
    payrollPage --> feval
    dash -- "GET /api/v1 + Bearer token (server side)" --> authCheck
    insightsPage --> authCheck
    exportRoute --> authCheck
    feval -- "POST, PATCH, DELETE" --> authCheck
    authCheck --> users
    authCheck --> beval --> services --> query
    query --> emp
    query --> pay
    org -- "1 to many" --- users
    org -- "1 to many" --- emp
    emp -- "1 to many" --- pay

    style out stroke-dasharray: 5 5
```
