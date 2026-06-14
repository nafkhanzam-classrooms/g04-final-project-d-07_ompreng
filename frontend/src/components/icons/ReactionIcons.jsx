const base = {
  width: 18, height: 18, viewBox: "0 0 24 24", fill: "none",
  stroke: "currentColor", strokeWidth: 1.75,
  strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true,
};

export function ReactionThumbsUpIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M7 10v11" />
      <path d="M7 11l4-7a2 2 0 0 1 3.7 1.1V9h4.2a2 2 0 0 1 2 2.4l-1.4 6.6a2 2 0 0 1-2 1.6H7" />
    </svg>
  );
}

export function ReactionThumbsDownIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M17 14V3" />
      <path d="M17 13l-4 7a2 2 0 0 1-3.7-1.1V15H5.1a2 2 0 0 1-2-2.4l1.4-6.6a2 2 0 0 1 2-1.6H17" />
    </svg>
  );
}

export function ReactionHeartIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M12 20.3 4.2 12.5a4.5 4.5 0 0 1 6.4-6.4l1.4 1.4 1.4-1.4a4.5 4.5 0 0 1 6.4 6.4Z" />
    </svg>
  );
}

export function ReactionLaughIcon(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M8 14a4 4 0 0 0 8 0Z" />
      <path d="M8.5 9.5h.01" />
      <path d="M15.5 9.5h.01" />
    </svg>
  );
}

export function ReactionQuestionIcon(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M9.2 9.2a2.8 2.8 0 0 1 5.4 1c0 1.9-2.8 2.5-2.8 4" />
      <path d="M12 17h.01" />
    </svg>
  );
}

export const reactionConfig = {
  agree: { label: "Agree", Icon: ReactionThumbsUpIcon },
  disagree: { label: "Disagree", Icon: ReactionThumbsDownIcon },
  like: { label: "Like", Icon: ReactionHeartIcon },
  funny: { label: "Funny", Icon: ReactionLaughIcon },
  confused: { label: "Confused", Icon: ReactionQuestionIcon },
};
