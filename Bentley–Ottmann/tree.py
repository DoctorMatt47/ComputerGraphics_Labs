# bintrees: 2.0.2, extracted from:
# http://pypi.python.org/pypi/bintrees

from operator import attrgetter
_sentinel = object()


class _ABCTree(object):
    def __init__(self, cmp=None, cmp_data=None):
        """T.__init__(...) initializes T; see T.__class__.__doc__ for signature"""
        self._root = None
        self._count = 0
        if cmp is None:
            def cmp(cmp_data, a, b):
                if a < b:
                    return -1
                elif a > b:
                    return 1
                else:
                    return 0
        self._cmp = cmp
        self._cmp_data = cmp_data

    def clear(self):
        """T.clear() -> None.  Remove all items from T."""
        def _clear(node):
            if node is not None:
                _clear(node.left)
                _clear(node.right)
                node.free()
        _clear(self._root)
        self._count = 0
        self._root = None

    @property
    def count(self):
        """Get items count."""
        return self._count

    def _get_value_or_sentinel(self, key):
        node = self._root
        while node is not None:
            cmp = self._cmp(self._cmp_data, key, node.key)
            if cmp == 0:
                return node.value
            elif cmp < 0:
                node = node.left
            else:
                node = node.right
        return _sentinel

    def get_value(self, key):
        value = self._get_value_or_sentinel(key)
        if value is _sentinel:
            raise KeyError(str(key))
        return value

    def pop_item(self):
        """T.pop_item() -> (k, v), remove and return some (key, value) pair as a
        2-tuple; but raise KeyError if T is empty.
        """
        if self.is_empty():
            raise KeyError("pop_item(): tree is empty")
        node = self._root
        while True:
            if node.left is not None:
                node = node.left
            elif node.right is not None:
                node = node.right
            else:
                break
        key = node.key
        value = node.value
        self.remove(key)
        return key, value
    popitem = pop_item  # for compatibility  to dict()

    def min_item(self):
        """Get item with min key of tree, raises ValueError if tree is empty."""
        if self.is_empty():
            raise ValueError("Tree is empty")
        node = self._root
        while node.left is not None:
            node = node.left
        return node.key, node.value

    def max_item(self):
        """Get item with max key of tree, raises ValueError if tree is empty."""
        if self.is_empty():
            raise ValueError("Tree is empty")
        node = self._root
        while node.right is not None:
            node = node.right
        return node.key, node.value

    def succ_item(self, key, default=_sentinel):
        """Get successor (k,v) pair of key, raises KeyError if key is max key
        or key does not exist. optimized for pypy.
        """
        # removed graingets version, because it was little slower on CPython and much slower on pypy
        # this version runs about 4x faster with pypy than the Cython version
        # Note: Code sharing of succ_item() and ceiling_item() is possible, but has always a speed penalty.
        node = self._root
        succ_node = None
        while node is not None:
            cmp = self._cmp(self._cmp_data, key, node.key)
            if cmp == 0:
                break
            elif cmp < 0:
                if (succ_node is None) or self._cmp(self._cmp_data, node.key, succ_node.key) < 0:
                    succ_node = node
                node = node.left
            else:
                node = node.right

        if node is None:  # stay at dead end
            if default is _sentinel:
                raise KeyError(str(key))
            return default
        # found node of key
        if node.right is not None:
            # find smallest node of right subtree
            node = node.right
            while node.left is not None:
                node = node.left
            if succ_node is None:
                succ_node = node
            elif self._cmp(self._cmp_data, node.key, succ_node.key) < 0:
                succ_node = node
        elif succ_node is None:  # given key is biggest in tree
            if default is _sentinel:
                raise KeyError(str(key))
            return default
        return succ_node.key, succ_node.value

    def prev_item(self, key, default=_sentinel):
        """Get predecessor (k,v) pair of key, raises KeyError if key is min key
        or key does not exist. optimized for pypy.
        """
        # removed graingets version, because it was little slower on CPython and much slower on pypy
        # this version runs about 4x faster with pypy than the Cython version
        # Note: Code sharing of prev_item() and floor_item() is possible, but has always a speed penalty.
        node = self._root
        prev_node = None

        while node is not None:
            cmp = self._cmp(self._cmp_data, key, node.key)
            if cmp == 0:
                break
            elif cmp < 0:
                node = node.left
            else:
                if (prev_node is None) or self._cmp(self._cmp_data, prev_node.key, node.key) < 0:
                    prev_node = node
                node = node.right

        if node is None:  # stay at dead end (None)
            if default is _sentinel:
                raise KeyError(str(key))
            return default
        # found node of key
        if node.left is not None:
            # find biggest node of left subtree
            node = node.left
            while node.right is not None:
                node = node.right
            if prev_node is None:
                prev_node = node
            elif self._cmp(self._cmp_data, prev_node.key, node.key) < 0:
                prev_node = node
        elif prev_node is None:  # given key is smallest in tree
            if default is _sentinel:
                raise KeyError(str(key))
            return default
        return prev_node.key, prev_node.value

    def __repr__(self):
        """T.__repr__(...) <==> repr(x)"""
        tpl = "%s({%s})" % (self.__class__.__name__, '%s')
        return tpl % ", ".join(("%r: %r" % item for item in self.items()))

    def __contains__(self, key):
        """k in T -> True if T has a key k, else False"""
        return self._get_value_or_sentinel(key) is not _sentinel

    def __len__(self):
        """T.__len__() <==> len(x)"""
        return self.count

    def is_empty(self):
        """T.is_empty() -> False if T contains any items else True"""
        return self.count == 0

    def set_default(self, key, default=None):
        """T.set_default(k[,d]) -> T.get(k,d), also set T[k]=d if k not in T"""
        value = self._get_value_or_sentinel(key)
        if value is _sentinel:
            self.insert(key, default)
            return default
        return value
    setdefault = set_default  # for compatibility to dict()

    def get(self, key, default=None):
        """T.get(k[,d]) -> T[k] if k in T, else d.  d defaults to None."""

        value = self._get_value_or_sentinel(key)
        if value is _sentinel:
            return default
        return value

    def pop(self, key, *args):
        """T.pop(k[,d]) -> v, remove specified key and return the corresponding value.
        If key is not found, d is returned if given, otherwise KeyError is raised
        """
        if len(args) > 1:
            raise TypeError("pop expected at most 2 arguments, got %d" % (1 + len(args)))

        value = self._get_value_or_sentinel(key)
        if value is _sentinel:
            if len(args) == 0:
                raise KeyError(str(key))
            return args[0]

        self.remove(key)
        return value

    def prev_key(self, key, default=_sentinel):
        """Get predecessor to key, raises KeyError if key is min key
        or key does not exist.
        """
        item = self.prev_item(key, default)
        return default if item is default else item[0]

    def succ_key(self, key, default=_sentinel):
        """Get successor to key, raises KeyError if key is max key
        or key does not exist.
        """
        item = self.succ_item(key, default)
        return default if item is default else item[0]

    def pop_min(self):
        """T.pop_min() -> (k, v), remove item with minimum key, raise ValueError
        if T is empty.
        """
        item = self.min_item()
        self.remove(item[0])
        return item

    def pop_max(self):
        """T.pop_max() -> (k, v), remove item with maximum key, raise ValueError
        if T is empty.
        """
        item = self.max_item()
        self.remove(item[0])
        return item

    def min_key(self):
        """Get min key of tree, raises ValueError if tree is empty. """
        return self.min_item()[0]

    def max_key(self):
        """Get max key of tree, raises ValueError if tree is empty. """
        return self.max_item()[0]

    def key_slice(self, start_key, end_key, reverse=False):
        """T.key_slice(start_key, end_key) -> key iterator:
        start_key <= key < end_key.
        Yields keys in ascending order if reverse is False else in descending order.
        """
        return (k for k, v in self.iter_items(start_key, end_key, reverse=reverse))

    def iter_items(self,  start_key=None, end_key=None, reverse=False):
        """Iterates over the (key, value) items of the associated tree,
        in ascending order if reverse is True, iterate in descending order,
        reverse defaults to False"""
        # optimized iterator (reduced method calls) - faster on CPython but slower on pypy

        if self.is_empty():
            return []
        if reverse:
            return self._iter_items_backward(start_key, end_key)
        else:
            return self._iter_items_forward(start_key, end_key)

    def _iter_items_forward(self, start_key=None, end_key=None):
        for item in self._iter_items(left=attrgetter("left"), right=attrgetter("right"),
                                     start_key=start_key, end_key=end_key):
            yield item

    def _iter_items_backward(self, start_key=None, end_key=None):
        for item in self._iter_items(left=attrgetter("right"), right=attrgetter("left"),
                                     start_key=start_key, end_key=end_key):
            yield item

    def _iter_items(self, left=attrgetter("left"), right=attrgetter("right"), start_key=None, end_key=None):
        node = self._root
        stack = []
        go_left = True
        in_range = self._get_in_range_func(start_key, end_key)

        while True:
            if left(node) is not None and go_left:
                stack.append(node)
                node = left(node)
            else:
                if in_range(node.key):
                    yield node.key, node.value
                if right(node) is not None:
                    node = right(node)
                    go_left = True
                else:
                    if not len(stack):
                        return  # all done
                    node = stack.pop()
                    go_left = False

    def _get_in_range_func(self, start_key, end_key):
        if start_key is None and end_key is None:
            return lambda x: True
        else:
            if start_key is None:
                start_key = self.min_key()
            if end_key is None:
                return (lambda x: self._cmp(self._cmp_data, start_key, x) <= 0)
            else:
                return (lambda x: self._cmp(self._cmp_data, start_key, x) <= 0 and
                                  self._cmp(self._cmp_data, x, end_key) < 0)


# ------
# RBTree

class Node(object):
    """Internal object, represents a tree node."""
    __slots__ = ['key', 'value', 'red', 'left', 'right']

    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.red = True
        self.left = None
        self.right = None

    def free(self):
        self.left = None
        self.right = None
        self.key = None
        self.value = None

    def __getitem__(self, key):
        """N.__getitem__(key) <==> x[key], where key is 0 (left) or 1 (right)."""
        return self.left if key == 0 else self.right

    def __setitem__(self, key, value):
        """N.__setitem__(key, value) <==> x[key]=value, where key is 0 (left) or 1 (right)."""
        if key == 0:
            self.left = value
        else:
            self.right = value


class RBTree(_ABCTree):
    """
    RBTree implements a balanced binary tree with a dict-like interface.
    see: http://en.wikipedia.org/wiki/Red_black_tree
    """
    @staticmethod
    def is_red(node):
        if (node is not None) and node.red:
            return True
        else:
            return False

    @staticmethod
    def jsw_single(root, direction):
        other_side = 1 - direction
        save = root[other_side]
        root[other_side] = save[direction]
        save[direction] = root
        root.red = True
        save.red = False
        return save

    @staticmethod
    def jsw_double(root, direction):
        other_side = 1 - direction
        root[other_side] = RBTree.jsw_single(root[other_side], other_side)
        return RBTree.jsw_single(root, direction)

    def _new_node(self, key, value):
        """Create a new tree node."""
        self._count += 1
        return Node(key, value)

    def insert(self, key, value):
        """T.insert(key, value) <==> T[key] = value, insert key, value into tree."""
        if self._root is None:  # Empty tree case
            self._root = self._new_node(key, value)
            self._root.red = False  # make root black
            return

        head = Node()  # False tree root
        grand_parent = None
        grand_grand_parent = head
        parent = None  # parent
        direction = 0
        last = 0

        # Set up helpers
        grand_grand_parent.right = self._root
        node = grand_grand_parent.right
        # Search down the tree
        while True:
            if node is None:  # Insert new node at the bottom
                node = self._new_node(key, value)
                parent[direction] = node
            elif RBTree.is_red(node.left) and RBTree.is_red(node.right):  # Color flip
                node.red = True
                node.left.red = False
                node.right.red = False

            # Fix red violation
            if RBTree.is_red(node) and RBTree.is_red(parent):
                direction2 = 1 if grand_grand_parent.right is grand_parent else 0
                if node is parent[last]:
                    grand_grand_parent[direction2] = RBTree.jsw_single(grand_parent, 1 - last)
                else:
                    grand_grand_parent[direction2] = RBTree.jsw_double(grand_parent, 1 - last)

            # Stop if found
            if self._cmp(self._cmp_data, key, node.key) == 0:
                node.value = value  # set new value for key
                break

            last = direction
            direction = 0 if (self._cmp(self._cmp_data, key, node.key) < 0) else 1
            # Update helpers
            if grand_parent is not None:
                grand_grand_parent = grand_parent
            grand_parent = parent
            parent = node
            node = node[direction]

        self._root = head.right  # Update root
        self._root.red = False  # make root black

    def remove(self, key):
        """T.remove(key) <==> del T[key], remove item <key> from tree."""
        if self._root is None:
            raise KeyError(str(key))
        head = Node()  # False tree root
        node = head
        node.right = self._root
        parent = None
        grand_parent = None
        found = None  # Found item
        direction = 1

        # Search and push a red down
        while node[direction] is not None:
            last = direction

            # Update helpers
            grand_parent = parent
            parent = node
            node = node[direction]

            direction = 1 if (self._cmp(self._cmp_data, node.key, key) < 0) else 0

            # Save found node
            if self._cmp(self._cmp_data, key, node.key) == 0:
                found = node

            # Push the red node down
            if not RBTree.is_red(node) and not RBTree.is_red(node[direction]):
                if RBTree.is_red(node[1 - direction]):
                    parent[last] = RBTree.jsw_single(node, direction)
                    parent = parent[last]
                elif not RBTree.is_red(node[1 - direction]):
                    sibling = parent[1 - last]
                    if sibling is not None:
                        if (not RBTree.is_red(sibling[1 - last])) and (not RBTree.is_red(sibling[last])):
                            # Color flip
                            parent.red = False
                            sibling.red = True
                            node.red = True
                        else:
                            direction2 = 1 if grand_parent.right is parent else 0
                            if RBTree.is_red(sibling[last]):
                                grand_parent[direction2] = RBTree.jsw_double(parent, last)
                            elif RBTree.is_red(sibling[1-last]):
                                grand_parent[direction2] = RBTree.jsw_single(parent, last)
                            # Ensure correct coloring
                            grand_parent[direction2].red = True
                            node.red = True
                            grand_parent[direction2].left.red = False
                            grand_parent[direction2].right.red = False

        # Replace and remove if found
        if found is not None:
            found.key = node.key
            found.value = node.value
            parent[int(parent.right is node)] = node[int(node.left is None)]
            node.free()
            self._count -= 1

        # Update root and make it black
        self._root = head.right
        if self._root is not None:
            self._root.red = False
        if not found:
            raise KeyError(str(key))
