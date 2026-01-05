// Custom JavaScript for Tender-RAG-Lab Documentation

document.addEventListener('DOMContentLoaded', function() {
    // Add copy feedback for code blocks
    document.querySelectorAll('.md-clipboard').forEach(button => {
        button.addEventListener('click', function() {
            const originalTitle = this.getAttribute('title');
            this.setAttribute('title', 'Copied!');
            
            setTimeout(() => {
                this.setAttribute('title', originalTitle);
            }, 2000);
        });
    });
    
    // Add anchor links to headings
    document.querySelectorAll('article h2, article h3, article h4').forEach(heading => {
        if (heading.id) {
            const link = document.createElement('a');
            link.className = 'headerlink';
            link.href = '#' + heading.id;
            link.textContent = '¶';
            heading.appendChild(link);
        }
    });
});
