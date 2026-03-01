---
title: "How I Built This Site"
date: 2026-02-28
draft: false
tags: ["azure", "hugo", "devops", "dns", "godaddy"]
---

# How I Built This Site

This is the first post on meath.cloud — and what better way to kick things off than documenting exactly how I built it. This site is part of a larger goal: transitioning from a System Administration Manager background into cloud engineering, AI/ML, and data science. Every project I build along the way gets documented here.

Here's everything that went into getting this site live on Day 1.

---

## The Stack

- **Hugo** — static site generator, content written in Markdown
- **Hello Friend NG** — dark, developer-focused Hugo theme
- **Azure Static Web Apps** — free tier hosting on Microsoft Azure
- **GitHub Actions** — CI/CD pipeline that auto-deploys on every push
- **GoDaddy** — domain registrar for meath.cloud

---

## Setting Up the Tools

On macOS, everything starts with Homebrew. If you don't have it:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then installing the tools I needed was straightforward:

```bash
brew install azure-cli
brew install hugo
brew install git
brew install gh  # GitHub CLI — needed for authentication
```

After installing the GitHub CLI, authenticating was simple:

```bash
gh auth login
```

This handles GitHub authentication via browser, which is necessary since GitHub deprecated password-based authentication over HTTPS.

---

## Building the Hugo Site

With Hugo installed, scaffolding the site and adding the theme:

```bash
hugo new site . --force
git submodule add https://github.com/rhazdon/hugo-theme-hello-friend-ng.git themes/hello-friend-ng
```

The Hello Friend NG theme has a specific way it expects social icons to be configured in `hugo.toml` — each platform needs its own `[[params.social]]` block:

```toml
[[params.social]]
  name = "github"
  url  = "https://github.com/yourusername"

[[params.social]]
  name = "linkedin"
  url  = "https://www.linkedin.com/in/yourusername"
```

Getting this wrong throws a template rendering error. The `name` field has to be lowercase and match the theme's built-in SVG icon names exactly.

To test locally:

```bash
hugo server -D
# Site runs at http://localhost:1313
```

---

## Deploying to Azure Static Web Apps

In the Azure Portal I created a Static Web App, linked it to my GitHub repository, and set the build preset to Hugo. Azure automatically committed a GitHub Actions workflow file to the repo — this is the CI/CD pipeline that rebuilds and redeploys the site every time I push a change.

After deployment I pulled the workflow file down locally:

```bash
git pull
```

The `.github/workflows/` folder now contains the YAML pipeline file. Worth reading through — it's straightforward and a good introduction to how GitHub Actions works.

---

## The DNS Nightmare (GoDaddy Edition)

This is where things got interesting. Getting a custom domain working with GoDaddy and Azure Static Web Apps took some troubleshooting.

**Problem 1 — GoDaddy Parking Page**
Even after Azure validated my domain and DNS was pointing to Azure's IP (`3.33.130.190`), GoDaddy was intercepting traffic and serving their parking page. The fix was finding and deleting the parked DNS record in GoDaddy's DNS settings.

**Problem 2 — Site Unreachable After Deleting Parked Record**
Deleting the parked record also removed the A record pointing to Azure. Fixed by adding it back manually:
- Type: **A** | Name: **@** | Value: **3.33.130.190**

**Problem 3 — Too Many Redirects**
After getting the domain working, I started hitting redirect loops intermittently. The cause was GoDaddy's domain forwarding and Azure's HTTPS redirect fighting each other in a loop. The fix was removing GoDaddy forwarding entirely and letting Azure handle all redirects, with DNS set up as:
- **A record** `@` → `3.33.130.190`
- **CNAME** `www` → `your-app.azurestaticapps.net`

Both `meath.cloud` and `www.meath.cloud` were added as custom domains in Azure Static Web Apps, and Azure handles SSL automatically for both.

---

## Content Structure in Hugo

One thing worth noting for anyone else using this theme — the About page needs to be a flat file at `content/about.md`, not a folder with an `index.md` inside it. Using `content/about/index.md` caused Hugo to absorb it into the home page URL instead of generating `/about/` as its own page.

Running `hugo list all` is a useful diagnostic command that shows every page Hugo knows about and the exact permalink it generated:

```bash
hugo list all
```

---

## The CI/CD Loop

The workflow from here on is simple:

```bash
git add .
git commit -m "your message"
git push
```

GitHub Actions picks it up, builds the Hugo site, and deploys it to Azure. Usually live within 2-3 minutes. You can watch it happen in real time under the Actions tab in your GitHub repo.

---

## What's Next

This site is the foundation. From here the plan is to build out cloud engineering, AI/ML, and data science skills on Azure and document every step publicly. Next up: going deeper into Azure infrastructure, Infrastructure as Code with Bicep or Terraform, and writing Python automation to replace some of my existing PowerShell workflows.

Every lesson, every mistake, and every fix will end up here.