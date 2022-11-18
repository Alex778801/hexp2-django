select finopers.finopers, project.project, costTypes.costTypes, agents.agents, users.users
from

-- finopers
(select json_agg(t) as finopers
from (
select
    finoper.id as id,
    extract(epoch from moment) as ts,
    "costType_id" as ctId,
    "agentFrom_id" as agFromId,
    "agentTo_id" as agToId,
    owner_id as ownerId,
    amount,
    notes,
    count(photo.id)
from dbcore_finoper as finoper
left join dbcore_photo photo on finoper.id = photo."finOper_id"
where project_id=322
group by finoper.id) t) finopers,

-- project
(select json_agg(t) as project
from (
select
    id,
    name
from dbcore_project
where id=322) t) project,

-- costTypes
(select json_agg(t) as costTypes
from (
select
    id,
    coalesce(parent_id, -1) as pid,
    "order" as ord,
    name,
    "isOutcome" as out,
    color
from dbcore_costtype) t) costTypes,

-- agents
(select json_agg(t) as agents
from (select coalesce(parent_id, -1) as pid,
             "order"                 as ord,
             name
      from dbcore_agent) t) agents,

-- users
(select json_agg(t) as users
from (select us.id as id,
             username,
             color
      from auth_user as us
               left join ua_userattr ua on us.id = ua.user_id) t) users
