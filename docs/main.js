document.addEventListener('DOMContentLoaded', () => {
  const html = document.documentElement;
  const toggle = document.getElementById('theme-toggle');
  const icon = document.getElementById('theme-icon');

  const setTheme = (theme) => {
    html.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    icon.src = theme === 'light' ? 'moon.png' : 'sun.png';
  };

  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  setTheme(saved || (prefersDark ? 'dark' : 'light'));

  toggle.addEventListener('click', () => {
    const current = html.getAttribute('data-theme') || 'dark';
    setTheme(current === 'dark' ? 'light' : 'dark');
  });

  // Fetch and display commits (MODIFIED)
  fetchCommits();
  // Fetch and display AI Summary (NEW)
  fetchAISummary();
});

async function fetchCommits() {
  const timeline = document.getElementById('commit-timeline');
  if (!timeline) return;

  try {
    // FIX: Request exactly 3 commits to respect the requirement
    const response = await fetch('https://api.github.com/repos/apmckelvey/boat-man-shooters/commits?per_page=3');
    const commits = await response.json();

    if (!Array.isArray(commits) || commits.length === 0) {
      timeline.innerHTML = '<p>No recent commits found.</p>';
      return;
    }

    const ul = document.createElement('ul');

    // Display the commits
    commits.forEach(commit => {
      const li = document.createElement('li');
      // Ensure we use the author's commit date/name, not committer's (GitHub sometimes changes committer for merges)
      const date = new Date(commit.commit.author.date).toLocaleDateString();
      li.innerHTML = `
        <span class="date">${date}:</span>
        <span class="message">${commit.commit.message}</span>
        <span class="author">by ${commit.commit.author.name}</span>
      `;
      ul.appendChild(li);
    });
    timeline.appendChild(ul);
  } catch (error) {
    console.error('Error fetching commits:', error);
    timeline.innerHTML = '<p>Failed to load commit history.</p>';
  }
}

// NEW FUNCTION: Fetches the AI-generated summary from the docs/data folder
async function fetchAISummary() {
  const aiCard = document.getElementById('ai-insight');
  const aiText = document.getElementById('ai-text');

  // Path is relative to index.html in the docs/ folder
  try {
    const response = await fetch('data/ai_summary.json');

    if (!response.ok) throw new Error('No AI summary found');

    const data = await response.json();
    aiText.textContent = `"${data.summary}"`;
    aiCard.style.display = 'block';

  } catch (error) {
    console.warn('AI Summary file not available yet (check GitHub Actions for run status):', error);
    // Hide the card if no data exists yet
    aiCard.style.display = 'none';
  }
}