class History(list):
    """A list-like collection that facilitates some of the more common
    tasks that are required.

    It is basically a list of dicts for each epoch, that again
    contains a list of dicts for each batch. For convenience, it has
    enhanced slicing notation and some methods to write new items.

    To access items from history, you may pass a tuple of up to four
    items:

      1. Slices along the epochs.
      2. Selects columns from history epochs, may be a single one or a
      tuple of column names.
      3. Slices along the batches.
      4. Selects columns from history batchs, may be a single one or a
      tuple of column names.

    You may use a combination of the four items.

    If you select columns that are not present in all epochs/batches,
    only those epochs/batches are chosen that contain said columns. If
    this set is empty, a KeyError is raised.

    Examples
    --------
    >>> # ACCESSING ITEMS
    >>> # history of a fitted neural net
    >>> history = net.history
    >>> # get current epoch, a dict
    >>> history[-1]
    >>> # get train losses from all epochs, a list of floats
    >>> history[:, 'train_loss']
    >>> # get train and valid losses from all epochs, a list of tuples
    >>> history[:, ('train_loss', 'valid_loss')]
    >>> # get current batches, a list of dicts
    >>> history[-1, 'batches']
    >>> # get latest batch, a dict
    >>> history[-1, 'batches', -1]
    >>> # get train losses from current batch, a list of floats
    >>> history[-1, 'batches', :, 'train_loss']
    >>> # get train and valid losses from current batch, a list of tuples
    >>> history[-1, 'batches', :, ('train_loss', 'valid_loss')]

    >>> # WRITING ITEMS
    >>> # add new epoch row
    >>> history.new_epoch()
    >>> # add an entry to current epoch
    >>> history.record('my-score', 123)
    >>> # add a batch row to the current epoch
    >>> history.new_batch()
    >>> # add an entry to the current batch
    >>> history.record_batch('my-batch-score', 456)
    >>> # overwrite entry of current batch
    >>> history.record_batch('my-batch-score', 789)

    """

    def new_epoch(self):
        """Register a new epoch row."""
        self.append({'batches': []})

    def new_batch(self):
        """Register a new batch row for the current epoch."""
        self[-1]['batches'].append({})

    def record(self, attr, value):
        """Add a new value to the given column for the current
        epoch.

        """
        msg = "Call new_epoch before recording for the first time."
        assert len(self) > 0, msg
        self[-1][attr] = value

    def record_batch(self, attr, value):
        """Add a new value to the given column for the current
        batch.

        """
        self[-1]['batches'][-1][attr] = value

    def to_list(self):
        """Return history object as a list."""
        return list(self)

    def __getitem__(self, i):
        if isinstance(i, (int, slice)):
            return super().__getitem__(i)

        class __missingno:
            def __init__(self, e):
                self.e = e
            def __repr__(self):
                return 'missingno'

        def partial_index(l, idx):
            is_list_like = lambda x: isinstance(x, list)

            needs_unrolling = is_list_like(l) \
                    and len(l) > 0 and is_list_like(l[0])
            needs_indirection = is_list_like(l) \
                    and not isinstance(idx, (int, tuple, list, slice))

            if needs_unrolling or needs_indirection:
                return [partial_index(n, idx) for n in l]

            # join results of multiple indices
            if isinstance(idx, (tuple, list)):
                def incomplete_mapper(x):
                    for xs in x:
                        if type(xs) is __missingno:
                            return xs
                    return x
                zz = [partial_index(l, n) for n in idx]
                if is_list_like(l):
                    total_join = zip(*zz)
                    inner_join = list(map(incomplete_mapper, total_join))
                else:
                    total_join = tuple(zz)
                    inner_join = incomplete_mapper(total_join)
                return inner_join

            try:
                return l[idx]
            except KeyError as e:
                return __missingno(e)

        def filter_missing(x):
            if isinstance(x, list):
                children = [filter_missing(n) for n in x]
                filtered = list(filter(lambda x: type(x) != __missingno, children))

                if len(children) > 0 and len(filtered) == 0:
                    return next(filter(lambda x: type(x) == __missingno, children))
                return filtered
            return x

        x = self
        if isinstance(i, tuple):
            for part in i:
                x_dirty = partial_index(x, part)
                x = filter_missing(x_dirty)
                if type(x) is __missingno:
                    raise x.e
            return x
        raise ValueError("Invalid parameter type passed to index. "
                         "Pass string, int or tuple.")

