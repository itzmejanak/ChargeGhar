#!/usr/bin/env python3
"""
GitHub Branch Manager - A comprehensive tool for managing Git branches
Features:
- List all local and remote branches
- Interactive branch switching and pulling
- Show detailed diff before pulling
- Categorize changed, new, and deleted files
- Stash management
- Conflict detection and resolution helpers
- Branch comparison
- Commit history viewing
"""

import subprocess
import sys
import os
from typing import List, Tuple, Dict
from enum import Enum


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class FileStatus(Enum):
    """File change status types"""
    MODIFIED = "Modified"
    ADDED = "Added"
    DELETED = "Deleted"
    RENAMED = "Renamed"


class GitManager:
    """Main Git management class"""
    
    def __init__(self):
        self.current_branch = None
        self.repo_path = None
        self._verify_git_repo()
    
    def _verify_git_repo(self):
        """Verify we're in a git repository"""
        try:
            result = self._run_command("git rev-parse --show-toplevel")
            self.repo_path = result.strip()
            result = self._run_command("git rev-parse --abbrev-ref HEAD")
            self.current_branch = result.strip()
        except subprocess.CalledProcessError:
            print(f"{Colors.RED}❌ Error: Not a git repository{Colors.ENDC}")
            sys.exit(1)
    
    def _run_command(self, command: str, check=True) -> str:
        """Execute shell command and return output"""
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout
    
    def _run_command_with_status(self, command: str) -> Tuple[str, int]:
        """Execute command and return output with status code"""
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout, result.returncode
    
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}\n")
    
    def print_section(self, text: str):
        """Print section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {text}{Colors.ENDC}")
        print(f"{Colors.BLUE}{'-'*70}{Colors.ENDC}")
    
    def get_all_branches(self) -> Dict[str, List[str]]:
        """Get all local and remote branches"""
        local_branches = []
        remote_branches = []
        
        # Get local branches
        output = self._run_command("git branch")
        for line in output.split('\n'):
            if line.strip():
                branch = line.strip().replace('* ', '')
                local_branches.append(branch)
        
        # Get remote branches
        output = self._run_command("git branch -r")
        for line in output.split('\n'):
            if line.strip() and 'HEAD' not in line:
                branch = line.strip()
                remote_branches.append(branch)
        
        return {
            'local': local_branches,
            'remote': remote_branches
        }
    
    def display_branches(self):
        """Display all branches with formatting"""
        self.print_header("GIT BRANCHES")
        branches = self.get_all_branches()
        
        # Display current branch
        print(f"{Colors.GREEN}📍 Current Branch: {Colors.BOLD}{self.current_branch}{Colors.ENDC}\n")
        
        # Display local branches
        self.print_section("Local Branches")
        for i, branch in enumerate(branches['local'], 1):
            marker = "➜" if branch == self.current_branch else " "
            color = Colors.GREEN if branch == self.current_branch else Colors.YELLOW
            print(f"{color}{marker} [{i}] {branch}{Colors.ENDC}")
        
        # Display remote branches
        self.print_section("Remote Branches")
        for i, branch in enumerate(branches['remote'], 1):
            print(f"{Colors.CYAN}  [{i}] {branch}{Colors.ENDC}")
    
    def get_file_changes(self, target_branch: str) -> Dict[str, List[str]]:
        """Get categorized file changes between current branch and target"""
        changes = {
            'modified': [],
            'added': [],
            'deleted': [],
            'renamed': []
        }
        
        # Fetch latest changes
        self._run_command(f"git fetch origin {target_branch}", check=False)
        
        # Get diff summary
        output = self._run_command(
            f"git diff --name-status {self.current_branch}..origin/{target_branch}"
        )
        
        for line in output.split('\n'):
            if not line.strip():
                continue
            
            parts = line.split('\t')
            status = parts[0][0]
            
            if status == 'M':
                changes['modified'].append(parts[1])
            elif status == 'A':
                changes['added'].append(parts[1])
            elif status == 'D':
                changes['deleted'].append(parts[1])
            elif status == 'R':
                changes['renamed'].append(f"{parts[1]} -> {parts[2]}")
        
        return changes
    
    def display_file_changes(self, changes: Dict[str, List[str]]):
        """Display categorized file changes"""
        total = sum(len(files) for files in changes.values())
        
        if total == 0:
            print(f"{Colors.GREEN}✓ No changes detected. Branch is up to date!{Colors.ENDC}")
            return False
        
        print(f"\n{Colors.BOLD}📊 Total Changes: {total} files{Colors.ENDC}\n")
        
        if changes['modified']:
            print(f"{Colors.YELLOW}📝 Modified Files ({len(changes['modified'])}){Colors.ENDC}")
            for file in changes['modified']:
                print(f"   {Colors.YELLOW}M{Colors.ENDC}  {file}")
        
        if changes['added']:
            print(f"\n{Colors.GREEN}➕ New Files ({len(changes['added'])}){Colors.ENDC}")
            for file in changes['added']:
                print(f"   {Colors.GREEN}A{Colors.ENDC}  {file}")
        
        if changes['deleted']:
            print(f"\n{Colors.RED}🗑️  Deleted Files ({len(changes['deleted'])}){Colors.ENDC}")
            for file in changes['deleted']:
                print(f"   {Colors.RED}D{Colors.ENDC}  {file}")
        
        if changes['renamed']:
            print(f"\n{Colors.CYAN}↪️  Renamed Files ({len(changes['renamed'])}){Colors.ENDC}")
            for file in changes['renamed']:
                print(f"   {Colors.CYAN}R{Colors.ENDC}  {file}")
        
        return True
    
    def show_file_diff(self, filename: str, target_branch: str):
        """Show detailed diff for a specific file"""
        print(f"\n{Colors.BOLD}{'─'*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}📄 Diff for: {filename}{Colors.ENDC}")
        print(f"{Colors.BOLD}{'─'*70}{Colors.ENDC}\n")
        
        # Show colored diff
        diff_output = self._run_command(
            f"git diff {self.current_branch}..origin/{target_branch} -- {filename}"
        )
        
        for line in diff_output.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                print(f"{Colors.GREEN}{line}{Colors.ENDC}")
            elif line.startswith('-') and not line.startswith('---'):
                print(f"{Colors.RED}{line}{Colors.ENDC}")
            elif line.startswith('@@'):
                print(f"{Colors.CYAN}{line}{Colors.ENDC}")
            else:
                print(line)
    
    def review_modified_files(self, modified_files: List[str], target_branch: str) -> bool:
        """Review each modified file and get user confirmation"""
        if not modified_files:
            return True
        
        print(f"\n{Colors.BOLD}🔍 Reviewing Modified Files{Colors.ENDC}")
        print("You can review the changes before pulling.\n")
        
        for i, file in enumerate(modified_files, 1):
            print(f"\n{Colors.YELLOW}[{i}/{len(modified_files)}] {file}{Colors.ENDC}")
            
            while True:
                choice = input(f"View diff? (y=yes, s=skip, q=quit review): ").lower().strip()
                
                if choice == 'y':
                    self.show_file_diff(file, target_branch)
                    break
                elif choice == 's':
                    print(f"{Colors.CYAN}⏭️  Skipped{Colors.ENDC}")
                    break
                elif choice == 'q':
                    print(f"{Colors.BLUE}Exiting review...{Colors.ENDC}")
                    return True
                else:
                    print(f"{Colors.RED}Invalid choice. Please enter y, s, or q{Colors.ENDC}")
        
        return True
    
    def check_local_changes(self) -> bool:
        """Check if there are uncommitted local changes"""
        output = self._run_command("git status --porcelain")
        return len(output.strip()) > 0
    
    def stash_changes(self):
        """Stash current changes"""
        print(f"{Colors.YELLOW}💾 Stashing local changes...{Colors.ENDC}")
        self._run_command("git stash save 'Auto-stash before pull'")
        print(f"{Colors.GREEN}✓ Changes stashed successfully{Colors.ENDC}")
    
    def pull_branch(self, branch_name: str):
        """Pull changes from specified branch"""
        self.print_header(f"PULLING FROM: {branch_name}")
        
        # Get changes first
        changes = self.get_file_changes(branch_name)
        has_changes = self.display_file_changes(changes)
        
        if not has_changes:
            return
        
        # Review modified files
        if changes['modified']:
            print(f"\n{Colors.BOLD}Do you want to review the modified files?{Colors.ENDC}")
            review = input("Review diffs? (y/n): ").lower().strip()
            
            if review == 'y':
                self.review_modified_files(changes['modified'], branch_name)
        
        # Final confirmation
        print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}Ready to pull changes from: {Colors.GREEN}{branch_name}{Colors.ENDC}")
        confirm = input(f"{Colors.BOLD}Proceed with pull? (y/n): {Colors.ENDC}").lower().strip()
        
        if confirm != 'y':
            print(f"{Colors.RED}❌ Pull cancelled{Colors.ENDC}")
            return
        
        # Check for local changes
        if self.check_local_changes():
            print(f"\n{Colors.YELLOW}⚠️  You have uncommitted local changes{Colors.ENDC}")
            stash = input("Stash changes before pulling? (y/n): ").lower().strip()
            
            if stash == 'y':
                self.stash_changes()
            else:
                print(f"{Colors.RED}❌ Cannot pull with uncommitted changes{Colors.ENDC}")
                return
        
        # Perform the pull
        print(f"\n{Colors.CYAN}🔄 Pulling changes...{Colors.ENDC}")
        output, status = self._run_command_with_status(f"git pull origin {branch_name}")
        
        if status == 0:
            print(f"{Colors.GREEN}✅ Successfully pulled from {branch_name}!{Colors.ENDC}")
            print(output)
        else:
            print(f"{Colors.RED}❌ Pull failed with conflicts{Colors.ENDC}")
            print(output)
            self.show_conflict_help()
    
    def show_conflict_help(self):
        """Show help for resolving conflicts"""
        print(f"\n{Colors.YELLOW}🔧 Conflict Resolution Help:{Colors.ENDC}")
        print(f"1. Run: {Colors.CYAN}git status{Colors.ENDC} to see conflicted files")
        print(f"2. Edit conflicted files manually")
        print(f"3. Run: {Colors.CYAN}git add <file>{Colors.ENDC} after resolving")
        print(f"4. Run: {Colors.CYAN}git commit{Colors.ENDC} to complete the merge")
    
    def compare_branches(self, branch1: str, branch2: str):
        """Compare two branches"""
        self.print_header(f"COMPARING: {branch1} vs {branch2}")
        
        # Commits in branch2 not in branch1
        output = self._run_command(f"git log --oneline {branch1}..{branch2}")
        commits_ahead = output.strip().split('\n') if output.strip() else []
        
        # Commits in branch1 not in branch2
        output = self._run_command(f"git log --oneline {branch2}..{branch1}")
        commits_behind = output.strip().split('\n') if output.strip() else []
        
        print(f"{Colors.GREEN}📈 {branch2} is ahead by {len(commits_ahead)} commit(s){Colors.ENDC}")
        if commits_ahead and commits_ahead[0]:
            for commit in commits_ahead[:5]:
                print(f"   {commit}")
            if len(commits_ahead) > 5:
                print(f"   ... and {len(commits_ahead) - 5} more")
        
        print(f"\n{Colors.YELLOW}📉 {branch2} is behind by {len(commits_behind)} commit(s){Colors.ENDC}")
        if commits_behind and commits_behind[0]:
            for commit in commits_behind[:5]:
                print(f"   {commit}")
            if len(commits_behind) > 5:
                print(f"   ... and {len(commits_behind) - 5} more")
    
    def show_recent_commits(self, count: int = 10):
        """Show recent commits"""
        self.print_header("RECENT COMMITS")
        output = self._run_command(f"git log --oneline -n {count} --decorate --color=always")
        print(output)
    
    def switch_branch(self, branch_name: str):
        """Switch to a different branch"""
        if self.check_local_changes():
            print(f"{Colors.YELLOW}⚠️  You have uncommitted changes{Colors.ENDC}")
            action = input("(s)tash, (c)ommit, or (a)bort? ").lower().strip()
            
            if action == 's':
                self.stash_changes()
            elif action == 'c':
                print("Please commit your changes manually and try again")
                return
            else:
                print(f"{Colors.RED}❌ Branch switch cancelled{Colors.ENDC}")
                return
        
        print(f"{Colors.CYAN}🔄 Switching to {branch_name}...{Colors.ENDC}")
        output, status = self._run_command_with_status(f"git checkout {branch_name}")
        
        if status == 0:
            self.current_branch = branch_name
            print(f"{Colors.GREEN}✅ Switched to {branch_name}{Colors.ENDC}")
        else:
            print(f"{Colors.RED}❌ Failed to switch branch{Colors.ENDC}")
            print(output)


def main():
    """Main program loop"""
    git = GitManager()
    
    while True:
        git.print_header("GIT BRANCH MANAGER")
        print(f"{Colors.GREEN}Current Branch: {Colors.BOLD}{git.current_branch}{Colors.ENDC}")
        print(f"{Colors.CYAN}Repository: {git.repo_path}{Colors.ENDC}\n")
        
        print("🎯 Main Actions:")
        print("  1. List all branches")
        print("  2. Pull from a branch (with diff review)")
        print("  3. Switch branch")
        print("  4. Compare branches")
        print("  5. Show recent commits")
        print("  6. Check git status")
        print("  7. Refresh current branch info")
        print("  0. Exit")
        
        choice = input(f"\n{Colors.BOLD}Enter your choice: {Colors.ENDC}").strip()
        
        if choice == '1':
            git.display_branches()
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")
        
        elif choice == '2':
            branch = input(f"{Colors.BOLD}Enter branch name to pull from: {Colors.ENDC}").strip()
            if branch:
                git.pull_branch(branch)
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")
        
        elif choice == '3':
            git.display_branches()
            branch = input(f"\n{Colors.BOLD}Enter branch name to switch to: {Colors.ENDC}").strip()
            if branch:
                git.switch_branch(branch)
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")
        
        elif choice == '4':
            git.display_branches()
            branch1 = input(f"\n{Colors.BOLD}Enter first branch: {Colors.ENDC}").strip()
            branch2 = input(f"{Colors.BOLD}Enter second branch: {Colors.ENDC}").strip()
            if branch1 and branch2:
                git.compare_branches(branch1, branch2)
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")
        
        elif choice == '5':
            count = input(f"Number of commits to show (default 10): ").strip()
            count = int(count) if count.isdigit() else 10
            git.show_recent_commits(count)
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")
        
        elif choice == '6':
            git.print_header("GIT STATUS")
            output = git._run_command("git status")
            print(output)
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")
        
        elif choice == '7':
            git._verify_git_repo()
            print(f"{Colors.GREEN}✅ Branch info refreshed{Colors.ENDC}")
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")
        
        elif choice == '0':
            print(f"\n{Colors.GREEN}👋 Thank you for using Git Branch Manager!{Colors.ENDC}\n")
            sys.exit(0)
        
        else:
            print(f"{Colors.RED}❌ Invalid choice. Please try again.{Colors.ENDC}")
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.ENDC}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}👋 Goodbye!{Colors.ENDC}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error: {str(e)}{Colors.ENDC}\n")
        sys.exit(1)