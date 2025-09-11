// NAVIGATION FIX FOR UNIFIED DEPLOYMENT
// This script fixes all navigation links to work with /dashboard/ prefix

console.log('🔧 Navigation Fix Loading...');

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Fixing navigation links...');
    
    // Fix all navigation links
    const links = document.querySelectorAll('a[href]');
    let fixedCount = 0;
    
    links.forEach(link => {
        const href = link.getAttribute('href');
        let newHref = href;
        
        // Fix specific problematic links
        if (href === '/participants') {
            newHref = '/dashboard/participants';
            fixedCount++;
        } else if (href === '/statistics') {
            newHref = '/dashboard/statistics';
            fixedCount++;
        } else if (href === '/images') {
            newHref = '/dashboard/images';
            fixedCount++;
        } else if (href === '/exclusions') {
            newHref = '/dashboard/exclusions';
            fixedCount++;
        } else if (href === '/logout') {
            newHref = '/dashboard/logout';
            fixedCount++;
        } else if (href === '/login') {
            newHref = '/dashboard/login';
            fixedCount++;
        } else if (href === '/register') {
            newHref = '/dashboard/register';
            fixedCount++;
        }
        
        if (newHref !== href) {
            link.setAttribute('href', newHref);
            console.log(`🔧 Fixed: ${href} → ${newHref}`);
        }
    });
    
    console.log(`✅ Navigation fix complete! Fixed ${fixedCount} links`);
});

// Also fix API calls
const originalFetch = window.fetch;
window.fetch = function(url, options) {
    if (typeof url === 'string' && url.startsWith('/api/')) {
        url = '/dashboard' + url;
        console.log(`🔧 Fixed API call: ${url}`);
    }
    return originalFetch(url, options);
};
