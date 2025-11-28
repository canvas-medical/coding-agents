# Canvas Plugin Development Assistant Setup Guide
## For Non-Developers

This guide will help you install and use the Canvas Plugin Development Assistant in Claude Code, starting from scratch.

---

## What Is This Tool?

The Canvas Plugin Development Assistant helps you build Canvas Medical plugins by:
- Guiding you through a conversation to gather requirements
- Suggesting the right Canvas SDK components to use
- Helping you deploy and test plugins

You don't need to be a developer to use it - just answer questions about what you want to build!

---

## Prerequisites

Before starting, make sure you have:

1. **Claude Code installed** - You should be able to open and use Claude Code
2. **Python 3 installed** - Open a terminal and type `python3 --version` - you should see a version number
3. **Canvas CLI installed** - In terminal type `pip list | grep canvas` - you should see "canvas" with a version number
4. **A code directory** - Usually `~/code` (this guide assumes that)
5. **Git installed** - Type `git --version` in terminal - you should see a version number

---

## Step 1: Get the Plugin Files

**What we're doing:** Cloning the Canvas Medical repository to get the plugin files

**How to do it:**

1. Open **Terminal** (Applications > Utilities > Terminal on Mac)

2. Navigate to your code directory:
   ```bash
   cd ~/code
   ```

3. Check if you already have the canvas-medical repository:
   ```bash
   ls
   ```

4. **If you DON'T see `canvas-medical` in the list**, clone the repository:
   ```bash
   git clone https://github.com/canvas-medical/canvas-medical.git
   ```

   **What this does:** Downloads all the Canvas Medical code files to your computer in a folder called `canvas-medical`

   **Note:** You may need to authenticate with GitHub. If prompted:
   - Enter your GitHub username
   - Enter your GitHub personal access token (not your password)
   - If you don't have a token, ask your team lead or see GitHub's documentation on creating one

5. **If you already have the repository**, update it to get the latest files:
   ```bash
   cd canvas-medical
   git pull
   cd ..
   ```

   **What this does:** Downloads any new changes that have been made to the repository since you last cloned it

---

## Step 2: Locate the Plugin Files

**What we're doing:** Finding where the plugin files are stored

**The plugin files are located at:**
```
~/code/canvas-medical/coding-agents/claude-code/canvas-plugin-assistant
```

**To verify they're there, run:**
```bash
ls ~/code/canvas-medical/coding-agents/claude-code/canvas-plugin-assistant
```

**You should see:**
- A `.claude` folder
- A `README.md` file

---

## Step 3: Install the Plugin Manually

**What we're doing:** Creating a link so Claude Code can find and use the plugin

**Important:** The marketplace install commands in the README don't always work, so we'll install manually instead.

**Run these commands in Terminal:**

```bash
# Create the plugins directory if it doesn't exist
mkdir -p ~/.claude/plugins/repos

# Create a link to the plugin
ln -sf ~/code/canvas-medical/coding-agents/claude-code/canvas-plugin-assistant ~/.claude/plugins/repos/canvas-plugin-assistant
```

**What this does:**
- `mkdir -p` creates the folders where plugins go (if they don't exist already)
- `ln -sf` creates a shortcut/link so Claude Code can find the plugin

**To verify it worked:**
```bash
ls -la ~/.claude/plugins/repos/
```

You should see `canvas-plugin-assistant` in the list.

---

## Step 4: Set Up Your Canvas Credentials

**What we're doing:** Giving the plugin permission to access your Canvas instances

**You need:**
- Client ID (from your Canvas instance)
- Client Secret (from your Canvas instance)
- Root Password (your Canvas admin password)

**How to create the credentials file:**

1. Run this command to create the file:
   ```bash
   mkdir -p ~/.canvas
   nano ~/.canvas/credentials.ini
   ```

2. This opens a text editor. Type in your credentials like this:
   ```ini
   [my-test-instance]
   client_id=YOUR_CLIENT_ID_HERE
   client_secret=YOUR_CLIENT_SECRET_HERE
   root_password=YOUR_ADMIN_PASSWORD_HERE
   is_default=true
   ```

3. **Replace** the placeholder text with your actual credentials
   - You can add multiple instances if needed (just copy the pattern)
   - The `is_default=true` line marks which instance to use by default

4. Save and exit:
   - Press `Control + O` (that's the letter O, not zero) to save
   - Press `Enter` to confirm
   - Press `Control + X` to exit

**To verify it worked:**
```bash
cat ~/.canvas/credentials.ini
```

You should see your credentials file content.

---

## Step 5: Restart Claude Code

**What we're doing:** Making Claude Code recognize the newly installed plugin

### How to Completely Quit Claude Code:

**On Mac:**
1. Click on **Claude Code** in the menu bar (top left of screen)
2. Click **Quit Claude Code** (or press `Command + Q`)
3. Wait a few seconds to make sure it fully closes

**Alternative method:**
1. Press `Command + Tab` to see open applications
2. Find Claude Code
3. Press `Command + Q` while Claude Code is highlighted

**To verify Claude Code is closed:**
- Check the Dock - the Claude Code icon should NOT have a dot under it
- Or open Activity Monitor and search for "Claude" - it shouldn't be running

### Restart Claude Code:
1. Open Claude Code from your Applications folder or Dock
2. Wait for it to fully load

---

## Step 6: Start Using the Plugin!

**What we're doing:** Testing that everything works

**In Claude Code, try typing one of these commands:**

```
/new-plugin
```

This should start a guided conversation to help you build a plugin.

**Other available commands:**
- `/analyze-instance` - Analyze a Canvas instance configuration
- `/deploy` - Deploy a plugin to Canvas
- `/spec` - View your plugin specification
- `/coverage` - Check test coverage

---

## Quick Reference

### File Locations
- **Plugin files:** `~/code/canvas-medical/coding-agents/claude-code/canvas-plugin-assistant`
- **Installed plugin:** `~/.claude/plugins/repos/canvas-plugin-assistant`
- **Credentials:** `~/.canvas/credentials.ini`

### Useful Commands
```bash
# Clone the repository (first time only)
cd ~/code
git clone https://github.com/canvas-medical/canvas-medical.git

# Update the repository (if you already have it)
cd ~/code/canvas-medical
git pull

# Check if plugin is installed
ls ~/.claude/plugins/repos/

# Check credentials file
cat ~/.canvas/credentials.ini

# Check Canvas CLI is installed
canvas --version

# Check Python is installed
python3 --version
```

### Available Slash Commands in Claude Code
- `/new-plugin` - Start building a plugin
- `/analyze-instance` - Analyze Canvas instance
- `/deploy` - Deploy a plugin
- `/spec` - View plugin specification
- `/coverage` - Check test coverage

---

## What to Do Next

1. **Test the installation** by typing `/new-plugin` in Claude Code
2. **Gather your plugin requirements** before starting (know what you want to build)
3. **Have your Canvas credentials ready** if you need to analyze instances or deploy

---

**You're all set!** 🎉

The Canvas Plugin Development Assistant is now ready to help you build plugins through guided conversations in Claude Code.
