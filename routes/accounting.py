from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models import Payment, Expense, Booking

accounting_bp = Blueprint("accounting", __name__, url_prefix="/accounting")


def get_month_range(year, month):
    if month == 12:
        return date(year, month, 1), date(year + 1, 1, 1) - timedelta(days=1)
    return date(year, month, 1), date(year + 1, month, 1) - timedelta(days=1)


@accounting_bp.route("/")
@login_required
def index():
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    tahun = request.args.get("tahun", date.today().year, type=int)
    bulan = request.args.get("bulan", date.today().month, type=int)

    start_date, end_date = get_month_range(tahun, bulan)

    pemasukan = db.session.query(db.func.sum(Payment.jumlah)).filter(
        Payment.status == "lunas",
        Payment.tanggal_bayar >= start_date,
        Payment.tanggal_bayar <= end_date,
    ).scalar() or 0

    pengeluaran = db.session.query(db.func.sum(Expense.jumlah)).filter(
        Expense.tanggal >= start_date,
        Expense.tanggal <= end_date,
    ).scalar() or 0

    laba_rugi = pemasukan - pengeluaran

    daftar_pemasukan = Payment.query.filter(
        Payment.status == "lunas",
        Payment.tanggal_bayar >= start_date,
        Payment.tanggal_bayar <= end_date,
    ).order_by(Payment.tanggal_bayar.desc()).all()

    daftar_pengeluaran = Expense.query.filter(
        Expense.tanggal >= start_date,
        Expense.tanggal <= end_date,
    ).order_by(Expense.tanggal.desc()).all()

    # Chart data - 12 bulan
    bulan_names = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
    pemasukan_chart = []
    pengeluaran_chart = []

    for m in range(1, 13):
        s, e = get_month_range(tahun, m)
        p = db.session.query(db.func.sum(Payment.jumlah)).filter(
            Payment.status == "lunas",
            Payment.tanggal_bayar >= s,
            Payment.tanggal_bayar <= e,
        ).scalar() or 0
        pe = db.session.query(db.func.sum(Expense.jumlah)).filter(
            Expense.tanggal >= s,
            Expense.tanggal <= e,
        ).scalar() or 0
        pemasukan_chart.append(float(p))
        pengeluaran_chart.append(float(pe))

    return render_template("accounting/index.html",
        tahun=tahun, bulan=bulan,
        pemasukan=pemasukan, pengeluaran=pengeluaran, laba_rugi=laba_rugi,
        daftar_pemasukan=daftar_pemasukan,
        daftar_pengeluaran=daftar_pengeluaran,
        bulan_names=bulan_names,
        pemasukan_chart=pemasukan_chart,
        pengeluaran_chart=pengeluaran_chart,
        selected_bulan=date(tahun, bulan, 1).strftime("%B"))


@accounting_bp.route("/pengeluaran/tambah", methods=["GET", "POST"])
@login_required
def tambah_pengeluaran():
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        try:
            jumlah = float(request.form.get("jumlah", 0))
        except ValueError:
            flash("Jumlah harus angka.", "danger")
            from models import Vendor
            vendors = Vendor.query.order_by(Vendor.nama).all()
            return render_template("accounting/expense_form.html", vendors=vendors)

        if jumlah <= 0:
            flash("Jumlah harus lebih dari 0.", "danger")
            from models import Vendor
            vendors = Vendor.query.order_by(Vendor.nama).all()
            return render_template("accounting/expense_form.html", vendors=vendors)

        expense = Expense(
            kategori=request.form.get("kategori", "lainnya"),
            jumlah=jumlah,
            tanggal=datetime.strptime(request.form["tanggal"], "%Y-%m-%d").date() if request.form.get("tanggal") else date.today(),
            deskripsi=request.form.get("deskripsi"),
            vendor_id=request.form.get("vendor_id", type=int) or None,
        )
        db.session.add(expense)
        db.session.commit()
        flash("Pengeluaran berhasil dicatat.", "success")
        return redirect(url_for("accounting.index"))

    from models import Vendor
    vendors = Vendor.query.order_by(Vendor.nama).all()
    return render_template("accounting/expense_form.html", vendors=vendors)


@accounting_bp.route("/pengeluaran/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_pengeluaran(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    expense = Expense.query.get_or_404(id)

    if request.method == "POST":
        try:
            expense.jumlah = float(request.form.get("jumlah", 0))
        except ValueError:
            flash("Jumlah harus angka.", "danger")
            from models import Vendor
            vendors = Vendor.query.order_by(Vendor.nama).all()
            return render_template("accounting/expense_form.html", expense=expense, vendors=vendors)

        expense.kategori = request.form.get("kategori", "lainnya")
        expense.tanggal = datetime.strptime(request.form["tanggal"], "%Y-%m-%d").date() if request.form.get("tanggal") else date.today()
        expense.deskripsi = request.form.get("deskripsi")
        expense.vendor_id = request.form.get("vendor_id", type=int) or None
        db.session.commit()
        flash("Pengeluaran berhasil diperbarui.", "success")
        return redirect(url_for("accounting.index"))

    from models import Vendor
    vendors = Vendor.query.order_by(Vendor.nama).all()
    return render_template("accounting/expense_form.html", expense=expense, vendors=vendors)


@accounting_bp.route("/pengeluaran/hapus/<int:id>", methods=["POST"])
@login_required
def hapus_pengeluaran(id):
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    flash("Pengeluaran berhasil dihapus.", "success")
    return redirect(url_for("accounting.index"))


@accounting_bp.route("/laporan")
@login_required
def laporan():
    if current_user.role not in ("admin", "management"):
        flash("Akses ditolak.", "danger")
        return redirect(url_for("dashboard.index"))

    tahun = request.args.get("tahun", date.today().year, type=int)
    bulanan = []
    total_pemasukan = 0
    total_pengeluaran = 0

    for m in range(1, 13):
        s, e = get_month_range(tahun, m)
        p = db.session.query(db.func.sum(Payment.jumlah)).filter(
            Payment.status == "lunas",
            Payment.tanggal_bayar >= s,
            Payment.tanggal_bayar <= e,
        ).scalar() or 0
        pe = db.session.query(db.func.sum(Expense.jumlah)).filter(
            Expense.tanggal >= s,
            Expense.tanggal <= e,
        ).scalar() or 0
        bulanan.append({
            "bulan": date(tahun, m, 1).strftime("%B"),
            "pemasukan": float(p),
            "pengeluaran": float(pe),
            "laba": float(p - pe),
        })
        total_pemasukan += float(p)
        total_pengeluaran += float(pe)

    return render_template("accounting/laporan.html",
        tahun=tahun, bulanan=bulanan,
        total_pemasukan=total_pemasukan,
        total_pengeluaran=total_pengeluaran,
        total_laba=total_pemasukan - total_pengeluaran)
