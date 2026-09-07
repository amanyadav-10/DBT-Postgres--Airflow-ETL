{#
    By default dbt concatenates the target schema with any custom schema
    (e.g. "public_raw"). For this project we want exact schema names
    (raw, staging, marts) regardless of the target schema, which is the
    common override pattern recommended in dbt's own docs.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
