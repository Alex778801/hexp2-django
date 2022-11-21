
-- drop function path(bigint, regclass);

create or replace function path(parentId bigint, tbl regclass)
returns varchar(512)
language plpgsql
as
$$
declare
    res varchar(512);
    tmp varchar(512);
    pid bigint;
begin
    res = '';
    if parentId IS NOT NULL then
        EXECUTE 'select name, parent_id from ' || tbl || ' where id = ' || parentId into tmp, pid;
        select tmp || '/' || res into res;
        --
        while pid IS NOT NULL
            loop
                EXECUTE 'select name, parent_id from ' || tbl || ' where id = ' || pid into tmp, pid;
                select tmp || '/' || res into res;
            end loop;
        --
    end if;
    return res;
end;
$$;

-- project
select
    id,
    name,
    path(parent_id, 'dbcore_project')
from dbcore_project;

