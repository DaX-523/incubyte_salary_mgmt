# Diagrams

Derived from `REQUIREMENTS.md` (up to "NEXT STEPS and frontend views planning") and the code as
built. Deactivation stays `DELETE /employees/{id}`, which sets `is_active` to false, as line 51
says. `init.png` adds server-side pagination.

## Core data model

```mermaid
erDiagram
    EMPLOYEES ||--o{ PAYROLLS : "is paid through"

    EMPLOYEES {
        int id PK "filter"
        string name "filter"
        string email "unique, lowercase"
        decimal monthly_salary "local currency of country; sortable within a country"
        string country "filter; fixed once set; decides the currency"
        string department "derived from job_title"
        string job_title "filter; from a fixed list"
        boolean is_active "false = deactivated, never deleted"
        timestamp created_at
        timestamp updated_at
    }

    PAYROLLS {
        int id PK
        int employee_id FK "unique with month; fixed once set"
        date month "unique with employee_id; fixed once set"
        decimal base
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
    subgraph employees["Employees"]
        list["GET /employees<br/>month (required), id, name, country, job_title,<br/>sort_by, sort_order, page, page_size<br/>each row: employee + that month's payroll or null"]
        create["POST /employees<br/>department and currency derived"]
        read["GET /employees/{id}"]
        update["PATCH /employees/{id}<br/>country cannot change"]
        deactivate["DELETE /employees/{id}<br/>sets is_active to false"]
        pay["POST /employees/{id}/payrolls<br/>currency from country"]
    end

    subgraph payrolls["Payrolls"]
        payroll["GET /payrolls/{id}"]
        correct["PATCH /payrolls/{id}<br/>amounts and method only"]
    end

    subgraph insights["Insights"]
        status["GET /insights/payroll-status<br/>month, country, job_title<br/>paid vs total (chart)"]
        byTitle["GET /insights/pay-by-job-title<br/>country (required)<br/>headcount, lowest, highest"]
    end

    filters["GET /filters<br/>countries, job titles, payment methods"]

    errors["Errors: 404 not found · 409 duplicate email,<br/>duplicate month, inactive employee · 422 invalid input"]

    style errors stroke-dasharray: 5 5
```

## Requirements across the stack

```mermaid
flowchart LR
    hr(["HR user"])

    subgraph fe["Frontend (Next.js, shadcn/ui)"]
        dash["Dashboard /<br/>month (default: current) + filters<br/>paid vs total chart, paginated table"]
        insightsPage["Pay by job title /insights<br/>one country at a time"]
        employeePages["/employees/new, /employees/:id<br/>add, edit, record payroll, deactivate"]
        payrollPage["/payrolls/:id<br/>correct a payroll"]
        feval["Form validation<br/>(browser + server actions)"]
        errorPage["Error, loading and not-found pages"]
    end

    subgraph be["Backend (FastAPI)"]
        beval["Validation (Pydantic)"]
        services["Business rules<br/>derive department and currency,<br/>no payroll for inactive employees"]
        query["Filtering, sorting and pagination<br/>run in SQL"]
    end

    subgraph data["PostgreSQL"]
        emp[("EMPLOYEES")]
        pay[("PAYROLLS<br/>unique per employee + month")]
    end

    out["Left out on purpose:<br/>authentication, dedicated cache (Redis)"]

    hr --> dash
    hr --> insightsPage
    insightsPage -- "rank a job title by salary" --> dash
    dash --> employeePages --> payrollPage
    employeePages --> feval
    payrollPage --> feval
    dash -- "GET /api/v1 (server side)" --> beval
    insightsPage --> beval
    feval -- "POST, PATCH, DELETE" --> beval
    beval --> services --> query
    query --> emp
    query --> pay
    emp -- "1 to many" --- pay

    style out stroke-dasharray: 5 5
```
