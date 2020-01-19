

class Namespace:
    """
    The namespace decorator can be used to automatically instantiate inner classes.

    Inner classes are used to group functionality. The namespace decorator simplifies their use and provides some
    useful auxilliary attributes.


    Example:
    ========

    class Scope(SomeBaseClass):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._channel_count = 4

    @Namespace
    class measurement:
        @property
        def status(self):
            return self.root.send_command('status')

    @Namespace
    class acquisition:
        def start(self):
            self.root.send_command('acquisition:start')

    @Namespace
    class trigger:
        @Namespace
        class edge:
            @property
            def level(self):
                return self.root.send_command('trigger:edge:level?')

            @level.setter
            def level(self, value):
                self.root.send_command('trigger:edge:level {0}'.format(value))

    @Namespace.repeat('_channel_count')
    class channels:
        @property
        def offset(self):
            return self.root.send_command('channel{0}:offset?'.format(self.index))

        @offset.setter
        def offset(self, value):
            self.root.send_command('channel{0}:offset {1}'.format(self.index, value))
    """
    def __init__(self, cls):
        self.cls = cls

    def __get__(self, instance, owner):
        if instance is None:
            return self.cls

        # create instance
        namespace = self.cls()
        # parent
        namespace.parent_namespace = instance
        # root. instance is root if it does not contain a root attribute
        try:
            namespace.root = instance.root
        except AttributeError:
            namespace.root = instance

        # save it in the dictionary
        instance.__dict__[self.cls.__name__] = namespace
        return namespace

    @classmethod
    def repeat(cls, count):
        """
        Decorator used for IVI repeated capabilities.

        :param count: how often the capability shall be repeated.
        """
        class NamespaceRepeat:
            def __init__(self, cls):
                self.cls = cls
                self.count = count

            def __get__(self, instance, owner):
                if instance is None:
                    return self.cls

                # find root, root has no root attribute
                try:
                    root = instance.root
                except AttributeError:
                    root = instance

                # determine number of instances
                # if it is a string, check namespace container instance first, then root
                if isinstance(self.count, int):
                    if self.count <= 0:
                        raise Exception('Invalid value for count: {0}.'.format(self.count))
                elif isinstance(self.count, str):
                    value = getattr(instance, self.count, None)
                    if value is None:
                        value = getattr(root, self.count, 1)
                    self.count = value
                else:
                    raise Exception('Invalid value for count: {0}.'.format(self.count))

                # create instances
                namespaces = [self.cls() for ii in range(self.count)]
                for ii in range(len(namespaces)):
                    namespaces[ii].parent_namespace = instance
                    namespaces[ii].root = root
                    namespaces[ii].index = ii
                    
                # save it in the dictionary
                instance.__dict__[self.cls.__name__] = namespaces
                return namespaces

        return NamespaceRepeat
