import warnings
import datetime
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.utils import IntegrityError
from common.models import BmobUser
from common.models import Relation
from emis.models import Token, EmisUser


def run():

    # @transaction.atomic
    def do(table):
        if table is not None:
            # Change emis_auth_token foreign key
            if table == Token:
                print('Start saving all in table ' + str(table))
                t1 = datetime.datetime.now()

                table_objects = table.objects.all()
                for i in table_objects:
                    try:
                        user = EmisUser.objects.filter(username__contains=i.user_id)[0]
                        i.user_id = user.pk
                    except Exception as e:
                        print(e)
                        print(i.key + ' -> ' + str(i.user_id) + ",")
                table.objects.using('localhost').bulk_create(table_objects)

                t2 = datetime.datetime.now()
                print('Save time: ' + str(t2 - t1))
                print('Finish!')
            else:
                print('Start saving all in table ' + str(table))
                t1 = datetime.datetime.now()

                table_objects = table.objects.all()
                try:
                    table.objects.using('localhost').bulk_create(table_objects)
                except:
                    pass

                t2 = datetime.datetime.now()
                print('Save time: ' + str(t2 - t1))
                print('Finish!')

    warnings.simplefilter("ignore")
    ContentType.objects.using('localhost').all().delete()

    for i in ContentType.objects.all():
        do(i.model_class())


def m():
    relations = Relation.objects.all()
    # all_rels = []
    for each in relations:
        try:
            emis_user = EmisUser.objects.filter(username=each.emisuser_id)[0]
            bmob_user = BmobUser.objects.filter(bmob_user=each.bmobuser_id)[0]
            Relation.objects.using('localhost').create(emisuser_id=emis_user.id, bmobuser_id=bmob_user.id)
        except:
            print(str(each.id) + ": " + str(emis_user.username) + " | " + str(bmob_user.bmob_user) + " 唯一键约束，忽略")
        # all_rels.append(Relation(emisuser_id=emis_user.id, bmobuser_id=bmob_user.id))
    # Relation.objects.using('localhost').bulk_create(all_rels)
