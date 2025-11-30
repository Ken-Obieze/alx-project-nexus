import graphene

class Query(graphene.ObjectType):
    ping = graphene.String(default_value="PollR GraphQL API is live")

schema = graphene.Schema(query=Query)