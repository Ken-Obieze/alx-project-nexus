from django.contrib import admin
from .models import Election, Position, Candidate


class PositionInline(admin.TabularInline):
    """Inline admin for positions."""
    model = Position
    extra = 1
    fields = ['title', 'description', 'order_index']


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    """Admin configuration for Election model."""
    
    list_display = ['title', 'organization', 'status', 'start_at', 'end_at', 'get_total_votes', 'created_at']
    list_filter = ['status', 'result_visibility', 'created_at']
    search_fields = ['title', 'organization__name']
    readonly_fields = ['status', 'created_at', 'updated_at', 'get_total_votes', 'get_voter_turnout']
    inlines = [PositionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('organization', 'title', 'description')
        }),
        ('Schedule', {
            'fields': ('start_at', 'end_at', 'status')
        }),
        ('Settings', {
            'fields': ('result_visibility',)
        }),
        ('Statistics', {
            'fields': ('get_total_votes', 'get_voter_turnout'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_total_votes(self, obj):
        """Display total votes."""
        return obj.get_total_votes()
    get_total_votes.short_description = 'Total Votes'
    
    def get_voter_turnout(self, obj):
        """Display voter turnout."""
        return f"{obj.get_voter_turnout():.2f}%"
    get_voter_turnout.short_description = 'Voter Turnout'


class CandidateInline(admin.TabularInline):
    """Inline admin for candidates."""
    model = Candidate
    extra = 1
    fields = ['user', 'name', 'manifesto']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """Admin configuration for Position model."""
    
    list_display = ['title', 'election', 'order_index', 'get_candidates_count', 'get_total_votes']
    list_filter = ['election__status', 'created_at']
    search_fields = ['title', 'election__title']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CandidateInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('election', 'title', 'description', 'order_index')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_candidates_count(self, obj):
        """Display candidates count."""
        return obj.get_candidates_count()
    get_candidates_count.short_description = 'Candidates'
    
    def get_total_votes(self, obj):
        """Display total votes."""
        return obj.get_total_votes()
    get_total_votes.short_description = 'Total Votes'


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    """Admin configuration for Candidate model."""
    
    list_display = ['name', 'position', 'user', 'get_vote_count', 'created_at']
    list_filter = ['position__election__status', 'created_at']
    search_fields = ['name', 'user__email', 'position__title']
    readonly_fields = ['created_at', 'updated_at', 'get_vote_count', 'get_vote_percentage']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('position', 'user', 'name')
        }),
        ('Details', {
            'fields': ('manifesto', 'photo_url')
        }),
        ('Statistics', {
            'fields': ('get_vote_count', 'get_vote_percentage'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_vote_count(self, obj):
        """Display vote count."""
        return obj.get_vote_count()
    get_vote_count.short_description = 'Votes'
    
    def get_vote_percentage(self, obj):
        """Display vote percentage."""
        return f"{obj.get_vote_percentage():.2f}%"
    get_vote_percentage.short_description = 'Vote %'