# Diagrams

Derived from `REQUIREMENTS.md`, with `init.png` filling in details the log does not cover
(dashboard insight, server-side pagination).

## Core data model

```mermaid
erDiagram
    EMPLOYEES ||--o{ PAYROLLS : "is paid through"

    EMPLOYEES {
        int id PK "filter"
        string name "filter"
        string email
        decimal monthly_salary "filter: salary"
        string country "filter"
        string department
        boolean is_active
        timestamp last_transaction_at
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
        string payment_method
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
        dash["Configurable dashboard<br/>paid this month vs total employees"]
        controls["Filter controls<br/>month (default), id, name,<br/>country, salary"]
        feval["Validation"]
    end

    subgraph be["Backend (FastAPI)"]
        beval["Validation"]
        query["Filtering + pagination<br/>run on the server"]
    end

    subgraph data["Core data model"]
        emp[("EMPLOYEES")]
        pay[("PAYROLLS<br/>unique per employee + month")]
    end

    hr --> dash --> controls --> feval
    feval -- "month + filters + page" --> beval --> query
    query --> emp
    query --> pay
    emp -- "1 to many" --- pay
    ui -.- dash
```
