import { useState, useEffect, useRef } from 'react';
import type { Notice, Announcement } from '@/interfaces/inform';
import { InformCate } from '@/interfaces/inform';
import { requestListUnreadAnnouncement, requestListUnreadInform } from '@/request/inform';

interface PaginationParams {
  current: number;
  pageSize: number;
  total?: number;
}

const useInform = () => {
  const refreshNoticeTimer = useRef<NodeJS.Timeout | null>(null);
  const refreshAnnouncementTimer = useRef<NodeJS.Timeout | null>(null);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [unreadNoticeList, setUnreadNoticeList] = useState<Notice[]>([]);
  const [unreadAnnouncementList, setUnreadAnnouncementList] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [pagination, setPagination] = useState<PaginationParams>({
    current: 1,
    pageSize: 5,
  });
  const [drawerVisible, setDrawerVisible] = useState<boolean>(false);

  const refreshUnreadInformList = async () => {
    setLoading(true);
    try {
      const offset = (pagination.current - 1) * pagination.pageSize;
      const { data } = await requestListUnreadInform(offset, pagination.pageSize);
      if (data && data.unread_informs) {
        setUnreadNoticeList(data.unread_informs);
        if (data.total !== undefined) {
          setPagination((prev) => ({
            ...prev,
            total: data.total,
          }));
        }
      } else {
        setUnreadNoticeList(data || []);
      }
    } catch (error) {
      console.error('Error fetching unread notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshUnreadAnnouncementList = async () => {
    setLoading(true);
    try {
      const { data } = await requestListUnreadAnnouncement();
      setUnreadAnnouncementList(data || []);
    } catch (error) {
      console.error('Error fetching unread announcements:', error);
    }
    setLoading(false);
  };

  const calculateUnreadCount = () => {
    return unreadNoticeList.length + unreadAnnouncementList.length;
  };

  const removeUnreadInform = (id: string | number, cate: string) => {
    if (cate === InformCate.Notice) {
      setUnreadNoticeList(unreadNoticeList.filter((item) => item.id !== id));
    } else if (cate === InformCate.Announcement) {
      setUnreadAnnouncementList(unreadAnnouncementList.filter((item) => item.id !== id));
    }
  };

  const handlePaginationChange = (page: number, pageSize?: number) => {
    setPagination((prev) => ({
      ...prev,
      current: page,
      pageSize: pageSize || prev.pageSize,
    }));
  };

  const resetAndRefresh = async () => {
    await refreshUnreadInformList();
    await refreshUnreadAnnouncementList();
  };

  const stopAutoRefresh = () => {
    if (refreshNoticeTimer.current) {
      clearInterval(refreshNoticeTimer.current);
      refreshNoticeTimer.current = null;
    }
    if (refreshAnnouncementTimer.current) {
      clearInterval(refreshAnnouncementTimer.current);
      refreshAnnouncementTimer.current = null;
    }
  };

  const startAutoRefresh = () => {
    stopAutoRefresh();

    refreshNoticeTimer.current = setInterval(() => {
      resetAndRefresh();
    }, 5000);
    refreshAnnouncementTimer.current = setInterval(() => {
      refreshUnreadAnnouncementList();
    }, 1000 * 60 * 2);
  };

  useEffect(() => {
    resetAndRefresh();

    if (!drawerVisible) {
      startAutoRefresh();
    }
    return () => {
      stopAutoRefresh();
    };
  }, []);

  useEffect(() => {
    if (drawerVisible) {
      stopAutoRefresh();
      resetAndRefresh();
    } else {
      startAutoRefresh();
    }
  }, [drawerVisible]);

  useEffect(() => {
    setUnreadCount(calculateUnreadCount());
  }, [unreadNoticeList, unreadAnnouncementList]);

  useEffect(() => {
    refreshUnreadInformList();
    refreshUnreadAnnouncementList();
  }, [pagination.current, pagination.pageSize]);

  return {
    unreadCount,
    unreadNoticeList,
    unreadAnnouncementList,
    removeUnreadInform,
    loading,
    resetAndRefresh,
    drawerVisible,
    setDrawerVisible,
    pagination,
    handlePaginationChange,
    refreshUnreadInformList,
    refreshUnreadAnnouncementList,
  };
};

export default useInform;
