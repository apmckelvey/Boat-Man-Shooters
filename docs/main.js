document.addEventListener('DOMContentLoaded', () => {
  const html = document.documentElement;
  const toggle = document.getElementById('theme-toggle');
  const icon = document.getElementById('theme-icon');

  const setTheme = (theme) => {
    html.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    icon.src = theme === 'light' ? 'Images/moon.png' : 'Images/sun.png';
  };

  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  setTheme(saved || (prefersDark ? 'dark' : 'light'));

  toggle.addEventListener('click', () => {
    const current = html.getAttribute('data-theme') || 'dark';
    setTheme(current === 'dark' ? 'light' : 'dark');
  });

  // Fetch and display commits
  fetchCommits();
});

async function fetchCommits() {
  const timeline = document.getElementById('commit-timeline');
  if (!timeline) return;

  try {
    const response = await fetch('https://api.github.com/repos/DaNoob8157/boat-man-shooters/commits?per_page=5');
    const commits = await response.json();

    if (!Array.isArray(commits) || commits.length === 0) {
      timeline.innerHTML = '<p>No recent commits found.</p>';
      return;
    }

    const ul = document.createElement('ul');
    commits.forEach(commit => {
      const li = document.createElement('li');
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