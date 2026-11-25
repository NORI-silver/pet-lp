P='tools/gen_rojin.py'
s=open(P,encoding='utf-8').read()
old='シニアの犬や猫を長期・終生で預かってくれる老犬ホーム・老猫ホームを{n}施設まとめました。"'
new='シニアの犬や猫を預かったり介護したりしてくれる老犬ホーム・老猫ホームを{n}施設まとめました。長期・終生か月ごとのお預かりかは施設ごとに違います。"'
assert s.count(old)==1
s=s.replace(old,new)
assert '"料金詳細"' in s and 'emg-intro' in s and '月ごとの老犬ホームのお預かり' in s and '預かり方（長期・終生・月ごと）' in s
open(P,'w',encoding='utf-8').write(s)
print('lede restored; main fact_cols/intro kept')
