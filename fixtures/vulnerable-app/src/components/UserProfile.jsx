// XSS via dangerouslySetInnerHTML
import React from 'react';

// BAD: dangerouslySetInnerHTML with unsanitized user input
export function UserProfile({ user }) {
  return (
    <div className="profile">
      <h1>{user.name}</h1>
      <div dangerouslySetInnerHTML={{ __html: user.bio }} />
      <div dangerouslySetInnerHTML={{ __html: user.description }} />
    </div>
  );
}

// BAD: Rendering user-supplied HTML from API response
export function Comment({ comment }) {
  return (
    <article>
      <p>{comment.author}</p>
      <div dangerouslySetInnerHTML={{ __html: comment.body }} />
    </article>
  );
}
