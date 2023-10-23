# contractBot

заготовленные типы контрактов:
Новые прописанные готовые сценарии для типов контракта:

• ОДНОРАЗОВЫЙ
-Кнопка «Подписать» включается автоматически 
-Кнопка «Подписать» является единоразовой: первый человек, нажавший «Подписать», становится исполнителем контракта
-После успешного поиска исполнителя, каждый администратор оповещается:
«Контракт №{номер_контракта} был подписан @{username_пользователя}
-Пользователь оповещается о том, что он подписал контракт

• КОНКУРС
-Кнопка «Подписать» включается автоматически 
-При нажатии пользователем «Подписать», каждому администратору отправляется сообщение «@{username_пользователя} отправил заявку на контракт №{номер_контракта}»
Под сообщением о поступившей заявке есть кнопка «Принять»
- В каждом контракте типа «КОНКУРС» у каждого администратора есть только 1 «голос», который он не сможет отозвать в случае, если уже отдал его кому-то из заявившихся. Конкурс заканчивается, когда последний администратор отдаст свой голос.
- Когда конкурс оканчивается, каждому администратору приходит оповещение с @username пользователя и номером подписанного контракта(также говорится, что участник выиграл конкурс)
- Под окончанием конкурса подразумевается подписание контракта с пользователем, получившим большинство голосов администраторов. Пользователь также оповещается о победе в конкурсе