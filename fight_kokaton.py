import os
import random
import sys
import time
import math
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:  # 修正这里：obj.rct → obj_rct
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
    imgs = {  # 0度から反時計回りに定義
        (+5, 0): img,  # 右
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
        (-5, 0): img0,  # 左
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  # 右下
    }

    def __init__(self, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数 xy：こうかとん画像の初期位置座標タプル
        """
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5, 0)  # こうかとんの向きを表すタプル

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
            self.dire = tuple(sum_mv)  # 移動方向を向きとして保存
        screen.blit(self.img, self.rct)


class Beam:
    """
    こうかとんが放つビームに関するクラス
    """
    def __init__(self, bird: Bird):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん（Birdインスタンス）
        """
        # こうかとんの向きに応じてビームの方向を設定
        vx, vy = bird.dire
        
        # ビームの速度を設定（向きに応じた速度）
        speed = 5
        self.vx = vx * speed // 5 if vx != 0 else speed
        self.vy = vy * speed // 5 if vy != 0 else 0
        
        # ビームの回転角度を計算
        if vx == 0 and vy == 0:  # 静止時は右向き
            angle = 0
        else:
            angle = math.degrees(math.atan2(-vy, vx))
        
        # ビーム画像を回転
        self.img = pg.transform.rotozoom(pg.image.load("fig/beam.png"), angle, 1.0)
        self.rct = self.img.get_rect()
        
        # こうかとんの向きに応じたビームの初期位置
        self.rct.centerx = bird.rct.centerx + bird.rct.width * vx // 5
        self.rct.centery = bird.rct.centery + bird.rct.height * vy // 5

    def update(self, screen: pg.Surface):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        if check_bound(self.rct) == (True, True):
            self.rct.move_ip(self.vx, self.vy)
            screen.blit(self.img, self.rct)


class Bomb:
    """
    爆弾に関するクラス
    """
    def __init__(self, color: tuple[int, int, int], rad: int):
        """
        引数に基づき爆弾円Surfaceを生成する
        引数1 color：爆弾円の色タプル
        引数2 rad：爆弾円の半径
        """
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.img = pg.transform.rotozoom(self.img, 0, 0.9)  # 爆弾サイズを0.9倍に
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Explosion:
    """
    爆発エフェクトに関するクラス
    """
    def __init__(self, center: tuple[int, int]):
        """
        爆発エフェクトの初期設定
        引数 center：爆発が発生する中心座標
        """
        # 爆発画像の読み込みと反転処理
        self.img1 = pg.image.load("fig/explosion.gif")
        self.img2 = pg.transform.flip(self.img1, True, False)  # 左右反転
        self.img3 = pg.transform.flip(self.img1, False, True)  # 上下反転
        self.img4 = pg.transform.flip(self.img1, True, True)   # 上下左右反転
        
        self.imgs = [self.img1, self.img2, self.img3, self.img4]
        self.rct = self.img1.get_rect()
        self.rct.center = center
        self.life = 20  # 爆発の表示時間

    def update(self, screen: pg.Surface):
        """
        爆発エフェクトを更新する
        引数 screen：画面Surface
        """
        if self.life > 0:
            # 爆発時間に応じて画像を切り替え
            img_index = (self.life // 5) % len(self.imgs)
            screen.blit(self.imgs[img_index], self.rct)
            self.life -= 1


class Score:
    """
    スコアを表示するクラス
    """
    def __init__(self):
        """
        スコア表示の初期設定
        """
        self.fonto = pg.font.Font(None, 50)
        self.color = (0, 0, 255)  # 青色
        self.score = 0
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        self.rct = self.img.get_rect()
        self.rct.center = (100, 50)  # 画面左上

    def update(self, screen: pg.Surface):
        """
        スコアを更新して表示する
        引数 screen：画面Surface
        """
        self.img = self.fonto.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.img, self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load("fig/pg_bg.jpg")
    bird = Bird((300, 200))
    bomb = Bomb((255, 0, 0), 10)
    beams = []
    explosions = []  # 爆発エフェクトのリスト
    score = Score()
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # スペースキー押下でBeamインスタンスを生成しリストに追加
                beams.append(Beam(bird))
        screen.blit(bg_img, [0, 0])
        
        # 爆弾とビームの衝突判定（複数ビーム対応）
        for beam in beams[:]:  # リストのコピーに対してイテレーション
            if bomb is not None and beam.rct.colliderect(bomb.rct):
                # 衝突したらビームをリストから削除し爆弾を消滅
                beams.remove(beam)
                # 爆発エフェクトを追加
                explosions.append(Explosion(bomb.rct.center))
                bomb = None
                # こうかとんが喜ぶエフェクト
                bird.change_img(6, screen)
                # スコアを増加
                score.score += 1
        
        # こうかとんと爆弾の衝突判定
        if bomb is not None:
            if bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                # Game Over 文字表示
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                pg.display.update()
                time.sleep(2)
                return

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        
        # ビームの更新（複数ビーム対応）
        for beam in beams[:]:
            beam.update(screen)
            # 画面外に出たビームを削除
            if check_bound(beam.rct) != (True, True):
                beams.remove(beam)
        
        # 爆弾の更新（Noneチェック）
        if bomb is not None:
            bomb.update(screen)
            
        # 爆発エフェクトの更新
        for explosion in explosions[:]:
            explosion.update(screen)
            # 爆発時間が終わったエフェクトを削除
            if explosion.life <= 0:
                explosions.remove(explosion)
            
        # スコアの更新と表示
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
