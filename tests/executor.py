from spec import Spec, eq_, skip
from mock import Mock

from invoke.context import Context
from invoke.executor import Executor
from invoke.collection import Collection
from invoke.tasks import Task, ctask


class Executor_(Spec):
    def setup(self):
        self.task1 = Task(Mock(return_value=7))
        self.task2 = Task(Mock(return_value=10), pre=['task1'])
        self.task3 = Task(Mock(), pre=['task1'])
        coll = Collection()
        coll.add_task(self.task1, name='task1')
        coll.add_task(self.task2, name='task2')
        coll.add_task(self.task3, name='task3')
        self.executor = Executor(collection=coll, context=Context())

    class init:
        "__init__"
        def needs_collection_and_context(self):
            coll = Collection()
            cont = Context()
            e = Executor(collection=coll, context=cont)
            assert e.collection is coll
            assert e.context is cont

    class execute:
        def base_case(self):
            self.executor.execute('task1')
            assert self.task1.body.called

        def kwargs(self):
            k = {'foo': 'bar'}
            self.executor.execute(name='task1', kwargs=k)
            self.task1.body.assert_called_once_with(**k)

        def pre_tasks(self):
            self.executor.execute(name='task2')
            eq_(self.task1.body.call_count, 1)

        def enabled_deduping(self):
            self.executor.execute(name='task2')
            self.executor.execute(name='task3')
            eq_(self.task1.body.call_count, 1)

        def disabled_deduping(self):
            self.executor.execute(name='task2', dedupe=False)
            self.executor.execute(name='task3', dedupe=False)
            eq_(self.task1.body.call_count, 2)

        def hands_collection_configuration_to_context(self):
            @ctask
            def mytask(ctx):
                eq_(ctx['my.config.key'], 'value')
            c = Collection(mytask)
            c.configure({'my.config.key': 'value'})
            Executor(collection=c, context=Context()).execute('mytask')

        def subcollection_configurations_are_merged_in(self):
            @ctask
            def mytask(ctx):
                eq_(ctx['unconflicted'], 'okay')
                eq_(ctx['also_unconflicted'], 'okay')
                # Sees inner, not outer, value
                eq_(ctx['conflicted'], 'I win')
            inner = Collection('inner')
            inner.configure({'unconflicted': 'okay', 'conflicted': 'I win'})
            ns = Collection(mytask, inner)
            ns.configure({'also_unconflicted': 'okay', 'conflicted': 'I lose'})
            Executor(collection=ns, context=Context()).execute('mytask')


    class returns_return_value_of_specified_task:
        def base_case(self):
            eq_(self.executor.execute(name='task1'), 7)

        def with_pre_tasks(self):
            eq_(self.executor.execute(name='task2'), 10)

        def with_post_tasks(self):
            skip()
