type compareRangeFn = (
  oldRange: [number, number],
  newRange: [number, number],
) => {
  add: [number, number][];
  remove: [number, number][];
};

export const compareRange: compareRangeFn = (
  oldRange: [number, number],
  newRange: [number, number],
) => {
  const [oldStart, oldEnd] = oldRange;
  const [newStart, newEnd] = newRange;

  // Identical ranges
  if (newStart === oldStart && newEnd === oldEnd) {
    return {
      add: [],
      remove: [],
    };
  }

  // Start points coincide
  if (newStart === oldStart) {
    // New contains old
    if (newEnd > oldEnd) {
      return {
        add: [[oldEnd, newEnd]],
        remove: [],
      };
    }
    // Old contains new
    if (newEnd < oldEnd) {
      return {
        add: [],
        remove: [[newEnd, oldEnd]],
      };
    }
    // New equals old
    if (newEnd === oldEnd) {
      return {
        add: [],
        remove: [],
      };
    }
  }

  // End points coincide
  if (newEnd === oldEnd) {
    // New contains old
    if (newStart < oldStart) {
      return {
        add: [[newStart, oldStart]],
        remove: [],
      };
    }
    // Old contains new
    if (newStart > oldStart) {
      return {
        add: [],
        remove: [[oldStart, newStart]],
      };
    }
  }

  // No overlap
  if (newStart > oldEnd || newEnd < oldStart) {
    return {
      add: [newRange],
      remove: [oldRange],
    };
  }

  // New contains old
  if (newStart < oldStart && newEnd > oldEnd) {
    return {
      add: [
        [newStart, oldStart],
        [oldEnd, newEnd],
      ],
      remove: [],
    };
  }

  // Old contains new
  if (newStart > oldStart && newEnd < oldEnd) {
    return {
      add: [],
      remove: [
        [oldStart, newStart],
        [newEnd, oldEnd],
      ],
    };
  }

  // New is to the left of old
  if (newStart < oldStart && newEnd < oldEnd) {
    return {
      add: [[newStart, oldStart]],
      remove: [[newEnd, oldEnd]],
    };
  }

  // New is to the right of old
  if (newStart > oldStart && newEnd > oldEnd) {
    return {
      add: [[oldEnd, newEnd]],
      remove: [[oldStart, newStart]],
    };
  }

  return {
    add: [],
    remove: [],
  };
};
