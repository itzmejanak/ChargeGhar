    print_status "✅ Pre-deployment validation passed"

    # Create rollback script
    create_rollback_script

    # Handle Git operations (clone or update)
    handle_git_operations

    # Run collectstatic before starting containers
    run_collectstatic