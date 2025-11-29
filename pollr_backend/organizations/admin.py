from django.contrib import admin
from .models import Organization, OrganizationMember


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Admin configuration for Organization model."""
    
    list_display = ['name', 'slug', 'owner', 'status', 'get_member_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'slug', 'owner__email']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'owner')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_member_count(self, obj):
        """Display member count."""
        return obj.get_member_count()
    get_member_count.short_description = 'Members'


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    """Admin configuration for OrganizationMember model."""
    
    list_display = ['user', 'organization', 'role', 'membership_status', 'invited_by', 'created_at']
    list_filter = ['membership_status', 'role', 'created_at']
    search_fields = ['user__email', 'organization__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Membership', {
            'fields': ('user', 'organization', 'role', 'membership_status')
        }),
        ('Additional Info', {
            'fields': ('invited_by',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )