from django.contrib import admin
from .models import Vote


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    """Admin configuration for Vote model."""
    
    list_display = ['get_voter', 'election', 'position', 'candidate', 'vote_token', 'created_at']
    list_filter = ['election__status', 'created_at']
    search_fields = ['vote_token', 'election__title', 'candidate__name']
    readonly_fields = ['vote_token', 'created_at']
    
    fieldsets = (
        ('Vote Information', {
            'fields': ('election', 'position', 'candidate')
        }),
        ('Voter Information', {
            'fields': ('voter', 'voter_user'),
            'description': 'One of voter or voter_user must be set'
        }),
        ('Verification', {
            'fields': ('vote_token', 'created_at')
        }),
    )
    
    def get_voter(self, obj):
        """Display voter."""
        if obj.voter:
            return obj.voter.user.email
        elif obj.voter_user:
            return f"{obj.voter_user.email} (Owner)"
        return "Unknown"
    get_voter.short_description = 'Voter'
    
    def has_add_permission(self, request):
        """Disable adding votes through admin."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable changing votes through admin."""
        return False