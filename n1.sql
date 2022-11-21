
-- drop function get_parents(bigint, char);

create or replace function get_parents(parentId bigint, tbl regclass)
returns char(255)
language plpgsql
as
$$
declare
   res char(255);
   tmp char(255);
   pid bigint;
begin
   res = '';
   if parentId IS NOT NULL then
       EXECUTE 'select name, parent_id from ' || tbl || ' where id = ' || parentId into tmp, pid;
       select tmp || '/' || res into res;
       --
       while pid IS NOT NULL loop
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
    get_parents(parent_id, 'dbcore_project')
from dbcore_project;

