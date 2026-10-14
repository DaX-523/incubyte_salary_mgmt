# Diagrams

Derived from `REQUIREMENTS.md` (up to the "updated filters" entry) and the current schema
(migration `0002`). `init.png` fills in details the log does not cover: the "paid vs total"
insight and server-side pagination.

## Core data model

```mermaid
erDiagram
    EMPLOYEES ||--o{ PAYROLLS : "is paid through"

    EMPLOYEES {
        int id PK "filter"
        string name "filter"
        string email
        decimal monthly_salary "local currency of country"
        string country "filter"
        string department
        string job_title "filter"
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    PAYROLLS {
        int id PK
        int employee_id FK "unique with month"
        date month "unique with employee_id; default view filter"
        decimal base
        decimal bonus
        decimal esops
        string currency
        string payment_method "bank_transfer or digital_wallet"
        timestamp created_at
        timestamp updated_at
    }
```

## Requirements across the stack

```mermaid
flowchart LR
    hr(["HR user"])

    subgraph fe["Frontend (Next.js)"]
        ui["Accessible component library<br/>(shadcn/ui)"]
        dash["Configurable dashboard<br/>chart of the month's data<br/>(paid vs total employees)"]
        controls["Filter controls<br/>month (default), id, name,<br/>country, job title"]
        feval["Validation"]
    end

    subgraph be["Backend (FastAPI)"]
        beval["Validation"]
        query["Filtering + pagination<br/>run on the server"]
    end

    subgraph data["PostgreSQL"]
        emp[("EMPLOYEES")]
        pay[("PAYROLLS<br/>unique per employee + month")]
    end

    out["Left out on purpose:<br/>authentication, dedicated cache (Redis)"]

    hr --> dash --> controls --> feval
    feval -- "month + filters + page" --> beval --> query
    query --> emp
    query --> pay
    emp -- "1 to many" --- pay
    ui -.- dash

    style out stroke-dasharray: 5 5
```
