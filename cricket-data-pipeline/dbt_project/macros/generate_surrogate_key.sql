{#
    A minimal, dependency-free surrogate key generator, so this project
    doesn't need to pull the external dbt_utils package just for one
    function. Concatenates the given columns (coalescing nulls to an
    empty string) and hashes the result with md5.

    Usage: {{ generate_surrogate_key(['col_a', 'col_b']) }}
#}
{% macro generate_surrogate_key(column_names) %}
    md5(
        {%- for col in column_names %}
        coalesce(cast({{ col }} as varchar), '')
        {%- if not loop.last %} || '-' || {% endif -%}
        {% endfor %}
    )
{% endmacro %}
