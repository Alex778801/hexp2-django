-- finopers
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
group by finoper.id;


-- project
select
    id,
    name
from dbcore_project;


-- costTypes
select
    id,
    coalesce(parent_id, -1) as pid,
    "order" as ord,
    name,
    "isOutcome" as out,
    color
from dbcore_costtype;


-- agents
select
    coalesce(parent_id, -1) as pid,
    "order" as ord,
    name
from dbcore_agent;


-- users
select
    us.id as id,
    username,
    color
from auth_user as us
left join ua_userattr ua on us.id = ua.user_id;
